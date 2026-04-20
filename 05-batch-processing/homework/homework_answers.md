# Module 5 Homework — Batch Processing with Spark

## Setup

```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder \
    .appName("HW5") \
    .master("local[*]") \
    .getOrCreate()

df = spark.read.parquet("data/yellow_taxi/")
```

---

## Question 1: What is the default number of partitions when reading a Parquet file?

```python
df = spark.read.parquet("yellow_tripdata_2021-01.parquet")
print(df.rdd.getNumPartitions())
```

**Answer:** Depends on file size and `spark.default.parallelism`. 
For a single local Parquet file it defaults to the number of CPU cores on the machine.
Typically `4` on a 4-core machine.

---

## Question 2: How many taxi trips were there on June 15, 2021?

```python
from pyspark.sql import functions as F

count = df \
    .filter(F.to_date("pickup_datetime") == "2021-06-15") \
    .count()

print(count)
```

**Answer:** `452,470`

---

## Question 3: Longest trip duration in hours for June 2021

```python
result = df \
    .filter(
        (F.month("pickup_datetime") == 6) &
        (F.year("pickup_datetime") == 2021)
    ) \
    .withColumn(
        "duration_hours",
        (F.unix_timestamp("dropoff_datetime") - F.unix_timestamp("pickup_datetime")) / 3600
    ) \
    .agg(F.max("duration_hours").alias("max_duration_hours"))

result.show()
```

**Answer:** `66.87 hours`

---

## Question 4: Most frequent pickup location zone on June 2021

```python
# Load zones lookup
zones = spark.read.csv(
    "taxi_zone_lookup.csv",
    header=True,
    inferSchema=True
)

trips_with_zones = df.join(
    zones,
    df.PULocationID == zones.LocationID,
    how="left"
)

top_zone = trips_with_zones \
    .filter(F.month("pickup_datetime") == 6) \
    .groupBy("Zone") \
    .count() \
    .orderBy("count", ascending=False)

top_zone.show(5)
```

**Answer:** `Crown Heights North`

---

## Question 5: Least frequent pickup zone

Using the same query above, scroll to the bottom:

```python
top_zone.orderBy("count", ascending=True).show(5)
```

**Answer:** `Jamaica Bay`

---

## Key Observations

**Lazy evaluation in action:** When I added `.filter()` before `.count()`, Spark
pushed the filter down to the file scan level — it never loaded the filtered-out rows
into memory. This is called **predicate pushdown** and it's why Spark + Parquet is fast.

**Partitions matter:** Reading a small file locally used 4 partitions (my CPU cores).
On a cluster with 20 workers, Spark would split it into more partitions for true parallelism.

**Spark SQL vs DataFrame API:** Both produce identical results and execution plans.
I prefer the DataFrame API for programmatic use and SQL for ad-hoc exploration.
