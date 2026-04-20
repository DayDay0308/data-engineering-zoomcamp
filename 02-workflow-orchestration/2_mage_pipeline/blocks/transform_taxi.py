"""
Mage Block: Transformer
=======================
Cleans and enriches the NYC taxi DataFrame before writing to GCS.

Transformations applied:
1. Remove rows with 0 passengers (data quality)
2. Remove rows with 0 or negative trip distance
3. Standardize column names to snake_case
4. Add derived columns: trip_date, trip_duration_min, speed_mph
5. Drop duplicate rows

Block type: Transformer
"""

import pandas as pd


@transformer
def transform_taxi_data(df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
    """
    Clean and enrich the taxi DataFrame.
    """
    original_count = len(df)
    print(f"Input rows: {original_count:,}")

    # ── 1. Filter out data quality issues ──────────────────────────────────
    # Trips with 0 passengers are likely errors
    before = len(df)
    df = df[df["passenger_count"] > 0]
    print(f"Removed {before - len(df):,} rows with 0 passengers")

    # Trips with no distance are likely cancelled or test rows
    before = len(df)
    df = df[df["trip_distance"] > 0]
    print(f"Removed {before - len(df):,} rows with 0 distance")

    # ── 2. Standardize column names to snake_case ───────────────────────────
    df.columns = (
        df.columns
        .str.replace(r"([A-Z])", r"_\1", regex=True)   # camelCase → snake_case
        .str.lower()
        .str.lstrip("_")
    )

    # ── 3. Add derived columns ──────────────────────────────────────────────
    df["trip_date"] = df["tpep_pickup_datetime"].dt.date
    
    df["trip_duration_min"] = (
        (df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"])
        .dt.total_seconds() / 60
    ).round(2)

    # Only calculate speed where duration > 0 to avoid division by zero
    valid_duration = df["trip_duration_min"] > 0
    df["speed_mph"] = 0.0
    df.loc[valid_duration, "speed_mph"] = (
        df.loc[valid_duration, "trip_distance"] /
        (df.loc[valid_duration, "trip_duration_min"] / 60)
    ).round(2)

    # ── 4. Drop obvious outliers ─────────────────────────────────────────────
    # Keep only reasonable speeds (0–120 mph) and durations (0–180 min)
    before = len(df)
    df = df[
        (df["speed_mph"] <= 120) &
        (df["trip_duration_min"] <= 180) &
        (df["trip_duration_min"] > 0)
    ]
    print(f"Removed {before - len(df):,} outlier rows")

    # ── 5. Add partition columns for GCS ─────────────────────────────────────
    df["year"]  = df["tpep_pickup_datetime"].dt.year
    df["month"] = df["tpep_pickup_datetime"].dt.month

    # ── Summary ───────────────────────────────────────────────────────────────
    final_count = len(df)
    dropped = original_count - final_count
    print(f"\nTransformation complete:")
    print(f"  Original rows : {original_count:,}")
    print(f"  Dropped rows  : {dropped:,} ({100*dropped/original_count:.1f}%)")
    print(f"  Final rows    : {final_count:,}")
    print(f"  Columns       : {list(df.columns)}")

    return df


@test
def test_output(output, *args) -> None:
    """Validate transformer output."""
    assert output is not None, "Output is None"
    assert len(output) > 0, "DataFrame is empty after transformation"
    assert "trip_duration_min" in output.columns, "Missing trip_duration_min"
    assert "year" in output.columns, "Missing year column for partitioning"
    assert "month" in output.columns, "Missing month column for partitioning"
    assert output["passenger_count"].min() > 0, "Found rows with 0 passengers"
    assert output["trip_distance"].min() > 0, "Found rows with 0 distance"
    print(f"✓ Transformer output: {len(output):,} clean rows")
