"""
Mage Block: Data Loader
=======================
Loads NYC Yellow Taxi data from the DataTalksClub GitHub releases.
Supports loading multiple months in one run.

Block type: Data Loader
"""

import pandas as pd
import requests
from io import BytesIO

# Taxi data column types — specify upfront to avoid dtype inference mistakes
TAXI_DTYPES = {
    "VendorID":                 pd.Int64Dtype(),
    "passenger_count":          pd.Int64Dtype(),
    "trip_distance":            float,
    "RatecodeID":               pd.Int64Dtype(),
    "store_and_fwd_flag":       str,
    "PULocationID":             pd.Int64Dtype(),
    "DOLocationID":             pd.Int64Dtype(),
    "payment_type":             pd.Int64Dtype(),
    "fare_amount":              float,
    "extra":                    float,
    "mta_tax":                  float,
    "tip_amount":               float,
    "tolls_amount":             float,
    "improvement_surcharge":    float,
    "total_amount":             float,
    "congestion_surcharge":     float,
}

PARSE_DATES = ["tpep_pickup_datetime", "tpep_dropoff_datetime"]


@data_loader
def load_taxi_data(*args, **kwargs) -> pd.DataFrame:
    """
    Load NYC Yellow Taxi data for Jan–Mar 2021.
    Returns a concatenated DataFrame of all months.
    """
    months = kwargs.get("months", [1, 2, 3])
    year = kwargs.get("year", 2021)
    
    base_url = (
        "https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/"
        "yellow_tripdata_{year}-{month:02d}.csv.gz"
    )
    
    dfs = []
    for month in months:
        url = base_url.format(year=year, month=month)
        print(f"Loading: {url}")
        
        df = pd.read_csv(
            url,
            sep=",",
            compression="gzip",
            dtype=TAXI_DTYPES,
            parse_dates=PARSE_DATES,
            low_memory=False,
        )
        
        print(f"  → {len(df):,} rows loaded for {year}-{month:02d}")
        dfs.append(df)
    
    combined = pd.concat(dfs, ignore_index=True)
    print(f"\nTotal rows loaded: {len(combined):,}")
    return combined


@test
def test_output(output, *args) -> None:
    """Validate the loader output."""
    assert output is not None, "Output is None"
    assert len(output) > 0, "DataFrame is empty"
    assert "tpep_pickup_datetime" in output.columns, "Missing pickup datetime column"
    assert "total_amount" in output.columns, "Missing total_amount column"
    print(f"✓ Loaded {len(output):,} rows with {len(output.columns)} columns")
