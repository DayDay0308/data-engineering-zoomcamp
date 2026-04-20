"""
Mage Block: Data Loader — GCS → BigQuery
=========================================
Reads partitioned Parquet from GCS data lake and loads into BigQuery.

This is the second pipeline: after the taxi data lands in GCS,
this pipeline picks it up and loads it into the data warehouse.

Block type: Data Exporter (writes to BigQuery)
"""

import os
from google.cloud import bigquery


# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ID   = os.environ.get("GCP_PROJECT_ID", "your-gcp-project-id")
DATASET_ID   = "ny_taxi_warehouse"
TABLE_ID     = "yellow_taxi_trips"
BUCKET_NAME  = os.environ.get("GCS_BUCKET_NAME", "your-project-data-lake-dezoomcamp")
GCS_PATH     = "ny_taxi/yellow"
# ─────────────────────────────────────────────────────────────────────────────


@data_exporter
def export_to_bigquery(*args, **kwargs) -> None:
    """
    Load all Parquet files from GCS into BigQuery using a load job.
    Uses WRITE_TRUNCATE so re-running this is idempotent.
    """
    client = bigquery.Client(project=PROJECT_ID)

    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    source_uri = f"gs://{BUCKET_NAME}/{GCS_PATH}/**/*.parquet"

    print(f"Loading from: {source_uri}")
    print(f"Destination : {table_ref}")

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # replace table
        autodetect=True,                                              # infer schema
    )

    load_job = client.load_table_from_uri(
        source_uris=source_uri,
        destination=table_ref,
        job_config=job_config,
    )

    print(f"Load job started: {load_job.job_id}")
    load_job.result()   # Wait for completion

    # Verify
    table = client.get_table(table_ref)
    print(f"\n✓ BigQuery load complete!")
    print(f"  Table   : {table_ref}")
    print(f"  Rows    : {table.num_rows:,}")
    print(f"  Size    : {table.num_bytes / 1024 / 1024:.1f} MB")


@test
def test_output(*args, **kwargs) -> None:
    """Confirm rows exist in BigQuery after load."""
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    query = f"SELECT COUNT(*) AS row_count FROM `{table_ref}`"
    result = client.query(query).result()
    row_count = list(result)[0].row_count
    
    assert row_count > 0, "BigQuery table is empty after load!"
    print(f"✓ BigQuery table has {row_count:,} rows")
