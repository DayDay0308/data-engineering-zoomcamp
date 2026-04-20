#!/usr/bin/env python3
"""
NYC Taxi Data Ingestion Script
================================
Downloads NYC TLC taxi trip data and ingests it into PostgreSQL.

Usage:
    python ingest_data.py \
        --user=root \
        --password=root \
        --host=localhost \
        --port=5432 \
        --db=ny_taxi \
        --table_name=yellow_taxi_trips \
        --url=<data_url>

Supports both CSV (.csv, .csv.gz) and Parquet (.parquet) formats.
"""

import argparse
import os
import time
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text


def parse_args():
    parser = argparse.ArgumentParser(description="Ingest NYC taxi data into PostgreSQL")
    parser.add_argument("--user",       required=True,  help="PostgreSQL username")
    parser.add_argument("--password",   required=True,  help="PostgreSQL password")
    parser.add_argument("--host",       required=True,  help="PostgreSQL host")
    parser.add_argument("--port",       required=True,  help="PostgreSQL port")
    parser.add_argument("--db",         required=True,  help="Database name")
    parser.add_argument("--table_name", required=True,  help="Target table name")
    parser.add_argument("--url",        required=True,  help="URL of the data file")
    return parser.parse_args()


def download_file(url: str) -> str:
    """Download file from URL and return local filename."""
    filename = url.split("/")[-1]
    print(f"Downloading {filename} from {url} ...")
    
    import urllib.request
    urllib.request.urlretrieve(url, filename)
    
    print(f"Download complete: {filename}")
    return filename


def get_engine(user: str, password: str, host: str, port: str, db: str):
    """Create SQLAlchemy engine for PostgreSQL."""
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(connection_string)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print(f"Connected to PostgreSQL: {result.fetchone()[0][:50]}...")
    
    return engine


def ingest_csv(filename: str, table_name: str, engine) -> None:
    """Ingest CSV or gzipped CSV file into PostgreSQL in chunks."""
    CHUNK_SIZE = 100_000
    
    # Read in chunks to handle large files
    chunk_iter = pd.read_csv(filename, iterator=True, chunksize=CHUNK_SIZE)
    
    total_rows = 0
    chunk_num = 0
    
    for chunk in chunk_iter:
        t_start = time.time()
        chunk_num += 1
        
        # Fix datetime columns (common in NYC taxi data)
        datetime_cols = [
            col for col in chunk.columns 
            if "datetime" in col.lower() or "time" in col.lower()
        ]
        for col in datetime_cols:
            try:
                chunk[col] = pd.to_datetime(chunk[col])
            except Exception:
                pass
        
        # First chunk: replace table (creates schema). Rest: append.
        if_exists = "replace" if chunk_num == 1 else "append"
        chunk.to_sql(table_name, con=engine, if_exists=if_exists, index=False)
        
        total_rows += len(chunk)
        elapsed = time.time() - t_start
        print(f"  Chunk {chunk_num}: inserted {len(chunk):,} rows | "
              f"Total: {total_rows:,} | Time: {elapsed:.2f}s")
    
    print(f"\nIngestion complete! Total rows: {total_rows:,}")


def ingest_parquet(filename: str, table_name: str, engine) -> None:
    """Ingest Parquet file into PostgreSQL."""
    print(f"Reading parquet file: {filename}")
    df = pd.read_parquet(filename)
    
    print(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"Columns: {list(df.columns)}")
    
    CHUNK_SIZE = 100_000
    total_rows = len(df)
    
    for i in range(0, total_rows, CHUNK_SIZE):
        t_start = time.time()
        chunk = df.iloc[i : i + CHUNK_SIZE]
        if_exists = "replace" if i == 0 else "append"
        chunk.to_sql(table_name, con=engine, if_exists=if_exists, index=False)
        elapsed = time.time() - t_start
        print(f"  Rows {i:,}–{min(i+CHUNK_SIZE, total_rows):,} inserted | Time: {elapsed:.2f}s")
    
    print(f"\nIngestion complete! Total rows: {total_rows:,}")


def main():
    args = parse_args()
    
    print("=" * 60)
    print("NYC Taxi Data Ingestion Pipeline")
    print("=" * 60)
    print(f"Target: {args.host}:{args.port}/{args.db} → table '{args.table_name}'")
    print(f"Source: {args.url}")
    print()
    
    # Download the file
    filename = download_file(args.url)
    
    # Connect to database
    engine = get_engine(args.user, args.password, args.host, args.port, args.db)
    
    # Ingest based on file type
    start_time = time.time()
    
    if filename.endswith(".parquet"):
        ingest_parquet(filename, args.table_name, engine)
    elif filename.endswith((".csv", ".csv.gz")):
        ingest_csv(filename, args.table_name, engine)
    else:
        raise ValueError(f"Unsupported file type: {filename}")
    
    total_time = time.time() - start_time
    print(f"\nTotal pipeline time: {total_time:.1f}s ({total_time/60:.1f} min)")
    
    # Cleanup downloaded file
    if os.path.exists(filename):
        os.remove(filename)
        print(f"Cleaned up: {filename}")


if __name__ == "__main__":
    main()
