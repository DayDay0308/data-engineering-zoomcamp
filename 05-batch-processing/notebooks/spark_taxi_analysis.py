"""
Spark Batch Processing — NYC Yellow Taxi Analysis
==================================================
Demonstrates core PySpark operations:
- Reading Parquet from GCS
- DataFrame transformations
- Spark SQL
- Aggregations and joins
- Writing results to BigQuery

Run locally:   python spark_taxi_analysis.py --local
Run on GCP:    python spark_taxi_analysis.py --gcs
"""

import argparse
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T


def create_spark_session(app_name: str, local: bool = True) -> SparkSession:
    """Create a SparkSession for local or GCP execution."""
    builder = SparkSession.builder.appName(app_name)

    if local:
        builder = builder.master("local[*]")
    else:
        # GCS + BigQuery connectors for Dataproc
        builder = builder \
            .config("spark.jars", "gs://spark-lib/bigquery/spark-bigquery-latest_2.12.jar")

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    print(f"Spark version: {spark.version}")
    print(f"Running on: {'local' if local else 'cluster'}")
    return spark


def load_data(spark: SparkSession, path: str):
    """Load NYC taxi Parquet data."""
    print(f"\nLoading data from: {path}")
    df = spark.read.parquet(path)
    print(f"Schema:")
    df.printSchema()
    print(f"Row count: {df.count():,}")
    return df


def clean_data(df):
    """Apply data quality filters and add derived columns."""
    print("\nCleaning data...")

    df_clean = df \
        .filter(F.col("passenger_count") > 0) \
        .filter(F.col("trip_distance") > 0) \
        .filter(F.col("total_amount") > 0) \
        .withColumn(
            "trip_duration_min",
            (F.unix_timestamp("tpep_dropoff_datetime") -
             F.unix_timestamp("tpep_pickup_datetime")) / 60
        ) \
        .filter(F.col("trip_duration_min") > 0) \
        .filter(F.col("trip_duration_min") < 180) \
        .withColumn(
            "speed_mph",
            F.col("trip_distance") / (F.col("trip_duration_min") / 60)
        ) \
        .filter(F.col("speed_mph") < 120) \
        .withColumn("pickup_date",  F.to_date("tpep_pickup_datetime")) \
        .withColumn("pickup_year",  F.year("tpep_pickup_datetime")) \
        .withColumn("pickup_month", F.month("tpep_pickup_datetime")) \
        .withColumn("pickup_hour",  F.hour("tpep_pickup_datetime"))

    print(f"Rows after cleaning: {df_clean.count():,}")
    return df_clean


def analyze_monthly_revenue(df):
    """Aggregate revenue and trip count by month."""
    print("\n=== Monthly Revenue Analysis ===")

    monthly = df \
        .groupBy("pickup_year", "pickup_month") \
        .agg(
            F.count("*").alias("trip_count"),
            F.round(F.sum("total_amount"), 2).alias("total_revenue"),
            F.round(F.avg("total_amount"), 2).alias("avg_fare"),
            F.round(F.avg("trip_distance"), 2).alias("avg_distance"),
            F.round(F.avg("trip_duration_min"), 1).alias("avg_duration_min")
        ) \
        .orderBy("pickup_year", "pickup_month")

    monthly.show(24, truncate=False)
    return monthly


def analyze_peak_hours(df):
    """Find the busiest hours of the day."""
    print("\n=== Peak Hours Analysis ===")

    peak_hours = df \
        .groupBy("pickup_hour") \
        .agg(
            F.count("*").alias("trip_count"),
            F.round(F.avg("total_amount"), 2).alias("avg_fare")
        ) \
        .orderBy("trip_count", ascending=False)

    peak_hours.show(24, truncate=False)
    return peak_hours


def analyze_with_sql(spark, df):
    """Demonstrate Spark SQL — same results as DataFrame API."""
    print("\n=== Spark SQL Analysis ===")

    df.createOrReplaceTempView("trips")

    result = spark.sql("""
        SELECT
            pickup_year,
            pickup_month,
            VendorID,
            COUNT(*)                            AS trips,
            ROUND(SUM(total_amount), 2)         AS revenue,
            ROUND(AVG(tip_amount / fare_amount) * 100, 1) AS tip_pct
        FROM trips
        WHERE fare_amount > 0
        GROUP BY pickup_year, pickup_month, VendorID
        ORDER BY pickup_year, pickup_month, trips DESC
    """)

    result.show(20, truncate=False)
    return result


def write_results(df, output_path: str, partition_cols: list = None):
    """Write DataFrame to Parquet."""
    print(f"\nWriting results to: {output_path}")
    writer = df.write.mode("overwrite")
    if partition_cols:
        writer = writer.partitionBy(*partition_cols)
    writer.parquet(output_path)
    print("Write complete.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true", default=True,
                        help="Run with local Spark master")
    parser.add_argument("--input",  default="data/yellow_taxi/",
                        help="Input Parquet path")
    parser.add_argument("--output", default="data/output/",
                        help="Output Parquet path")
    args = parser.parse_args()

    spark = create_spark_session("NYTaxiBatchAnalysis", local=args.local)

    # Load and clean
    df_raw   = load_data(spark, args.input)
    df_clean = clean_data(df_raw)

    # Analyses
    monthly  = analyze_monthly_revenue(df_clean)
    peaks    = analyze_peak_hours(df_clean)
    sql_results = analyze_with_sql(spark, df_clean)

    # Write monthly summary
    write_results(
        monthly,
        f"{args.output}/monthly_summary/",
        partition_cols=["pickup_year", "pickup_month"]
    )

    print("\nAll analyses complete.")
    spark.stop()


if __name__ == "__main__":
    main()
