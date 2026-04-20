# Module 5: Batch Processing with Apache Spark

## Overview

So far our pipeline handles data that's already in GCS and BigQuery. But what about
processing **massive datasets** — terabytes of data that can't fit in memory on one machine?

That's where **Apache Spark** comes in. Spark is a distributed computing framework that
splits data across many machines (a cluster) and processes them in parallel.

---

## What I Learned

### Why Spark?

| Scenario | Tool |
|----------|------|
| Data fits in memory (< a few GB) | pandas |
| Data in BigQuery, complex SQL | BigQuery SQL |
| Data is TBs, needs custom logic | **Apache Spark** |
| Real-time streaming | Spark Streaming / Kafka |

Spark is used when:
- Data is too large for a single machine
- You need complex transformations that SQL can't express
- You want to process data across a cluster in parallel

### How Spark Works

Spark breaks data into **partitions** and distributes them across worker nodes:

```
Driver (your code)
    ↓
Spark Master
    ↓
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Worker 1 │  │ Worker 2 │  │ Worker 3 │
│ Partition│  │ Partition│  │ Partition│
│  1, 4, 7 │  │  2, 5, 8 │  │  3, 6, 9 │
└──────────┘  └──────────┘  └──────────┘
```

Each worker processes its partitions independently. The driver collects results.

### RDDs vs DataFrames vs Datasets

| API | Language | Use case |
|-----|----------|----------|
| **RDD** | Low-level | Fine-grained control (rarely needed now) |
| **DataFrame** | Python/Scala/Java/R | Most common — like pandas but distributed |
| **Dataset** | Scala/Java | Type-safe DataFrames |

We use **DataFrames** (via PySpark) throughout this module.

### Lazy Evaluation

Spark doesn't execute transformations immediately. It builds a **logical plan**
and only runs when you call an **action**:

```python
# These are TRANSFORMATIONS (lazy — nothing runs yet)
df = spark.read.parquet("gs://bucket/yellow_taxi/")
df_filtered = df.filter(df.passenger_count > 0)
df_clean = df_filtered.select("pickup_datetime", "total_amount")

# This is an ACTION — now Spark runs everything
df_clean.count()       # triggers execution
df_clean.show()        # triggers execution
df_clean.write.parquet("output/")  # triggers execution
```

This allows Spark to optimize the entire pipeline before running.

### Spark SQL

You can query DataFrames with SQL:

```python
df.createOrReplaceTempView("trips")

result = spark.sql("""
    SELECT 
        DATE_TRUNC('month', pickup_datetime) AS month,
        COUNT(*) AS trip_count,
        SUM(total_amount) AS revenue
    FROM trips
    WHERE passenger_count > 0
    GROUP BY month
    ORDER BY month
""")
```

### GroupBy and Aggregations

```python
from pyspark.sql import functions as F

df.groupBy("vendor_id") \
  .agg(
      F.count("*").alias("trip_count"),
      F.sum("total_amount").alias("total_revenue"),
      F.avg("trip_distance").alias("avg_distance")
  ) \
  .orderBy("trip_count", ascending=False) \
  .show()
```

### Joins

```python
# Load zones lookup
zones = spark.read.csv("taxi_zone_lookup.csv", header=True, inferSchema=True)

# Join trips with zones
trips_with_zones = trips.join(
    zones.alias("pu"),
    trips.PULocationID == F.col("pu.LocationID"),
    how="left"
).join(
    zones.alias("do"),
    trips.DOLocationID == F.col("do.LocationID"),
    how="left"
)
```

---

## Folder Structure

```
05-batch-processing/
├── README.md
├── notebooks/
│   ├── 01_spark_intro.ipynb          # Spark basics, DataFrames
│   ├── 02_spark_sql.ipynb            # Spark SQL queries
│   ├── 03_spark_joins.ipynb          # Joining large datasets
│   └── 04_spark_gcs_bigquery.ipynb   # Read from GCS, write to BigQuery
└── homework/
    └── homework_answers.md
```

---

## How to Run Spark Locally

### Option 1: PySpark directly (simplest)

```bash
pip install pyspark

python - <<'EOF'
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("NYTaxiAnalysis") \
    .master("local[*]") \
    .getOrCreate()

df = spark.read.parquet("path/to/yellow_taxi/*.parquet")
df.printSchema()
df.show(5)
spark.stop()
EOF
```

### Option 2: Jupyter notebook

```bash
pip install pyspark jupyter

jupyter notebook notebooks/01_spark_intro.ipynb
```

### Option 3: Google Dataproc (cloud cluster)

```bash
# Create a Dataproc cluster
gcloud dataproc clusters create ny-taxi-cluster \
  --region=us-central1 \
  --num-workers=2 \
  --worker-machine-type=n1-standard-4

# Submit a PySpark job
gcloud dataproc jobs submit pyspark \
  --cluster=ny-taxi-cluster \
  --region=us-central1 \
  notebooks/04_spark_gcs_bigquery.py

# Delete cluster when done (important!)
gcloud dataproc clusters delete ny-taxi-cluster --region=us-central1
```

---

## Key PySpark Operations Reference

```python
from pyspark.sql import SparkSession, functions as F, types as T

# Start session
spark = SparkSession.builder.appName("App").master("local[*]").getOrCreate()

# Read
df = spark.read.parquet("path/")
df = spark.read.csv("path.csv", header=True, inferSchema=True)
df = spark.read.option("header", True).csv("path.csv")

# Inspect
df.printSchema()
df.show(5, truncate=False)
df.describe().show()
df.count()

# Select & filter
df.select("col1", "col2")
df.filter(df.col1 > 0)
df.filter((df.col1 > 0) & (df.col2.isNotNull()))
df.where("col1 > 0")

# Transform
df.withColumn("new_col", F.col("col1") * 2)
df.withColumnRenamed("old_name", "new_name")
df.drop("col_to_remove")

# Aggregations
df.groupBy("category").agg(F.count("*"), F.sum("amount"))

# Write
df.write.parquet("output/", mode="overwrite")
df.write.mode("overwrite").partitionBy("year", "month").parquet("output/")
```
