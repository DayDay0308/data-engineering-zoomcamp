"""
Mage Block: Data Exporter — GCS (Data Lake)
===========================================
Writes the cleaned taxi DataFrame to Google Cloud Storage
as partitioned Parquet files (partitioned by year/month).

File layout in GCS:
    gs://<bucket>/ny_taxi/yellow/
    ├── year=2021/
    │   ├── month=1/part.0.parquet
    │   ├── month=2/part.0.parquet
    │   └── month=3/part.0.parquet

Block type: Data Exporter
"""

import pyarrow as pa
import pyarrow.parquet as pq
from google.cloud import storage
import os


# ── Configuration — update these values ─────────────────────────────────────
BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "your-project-data-lake-dezoomcamp")
GCS_PATH    = "ny_taxi/yellow"
# ─────────────────────────────────────────────────────────────────────────────


@data_exporter
def export_to_gcs(df, *args, **kwargs) -> None:
    """
    Write DataFrame to GCS as partitioned Parquet, split by year and month.
    """
    import pandas as pd

    print(f"Exporting {len(df):,} rows to GCS bucket: {BUCKET_NAME}")
    print(f"Destination path: gs://{BUCKET_NAME}/{GCS_PATH}/")

    # Convert to PyArrow Table
    table = pa.Table.from_pandas(df, preserve_index=False)

    # Set up GCS filesystem
    gcs = pa.fs.GcsFileSystem()

    # Write partitioned dataset
    root_path = f"{BUCKET_NAME}/{GCS_PATH}"

    pq.write_to_dataset(
        table,
        root_path=root_path,
        partition_cols=["year", "month"],
        filesystem=gcs,
        use_deprecated_int96_timestamps=True,
        existing_data_behavior="overwrite_or_ignore",
    )

    print(f"✓ Export complete → gs://{root_path}/")
    
    # List what was written
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = list(bucket.list_blobs(prefix=GCS_PATH))
    print(f"\nFiles written to GCS ({len(blobs)} total):")
    for blob in blobs[:10]:  # show first 10
        size_kb = blob.size / 1024
        print(f"  gs://{BUCKET_NAME}/{blob.name}  ({size_kb:.1f} KB)")
    if len(blobs) > 10:
        print(f"  ... and {len(blobs) - 10} more")


@test
def test_output(*args, **kwargs) -> None:
    """Verify files exist in GCS after export."""
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = list(bucket.list_blobs(prefix=GCS_PATH))
    assert len(blobs) > 0, f"No files found at gs://{BUCKET_NAME}/{GCS_PATH}/"
    print(f"✓ {len(blobs)} Parquet files confirmed in GCS")
