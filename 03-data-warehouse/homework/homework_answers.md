# Module 3 Homework — BigQuery & Data Warehouse

## Setup

Data loaded into BigQuery from GCS Parquet files using an external table, then
copied into a native partitioned table for performance testing.

Dataset: NYC Yellow Taxi 2022 (Jan–Jun)

---

## Question 1: Count of records for the 2022 Yellow Taxi data

```sql
SELECT COUNT(*) FROM `ny_taxi_warehouse.yellow_trips_external`;
```

**Answer:** `43,244,696`

---

## Question 2: Count of distinct affiliated_base_number in external vs native table

The interesting thing here is that BigQuery reports **0 bytes** for the external table
query because it can't estimate the size without reading from GCS. The native table
shows the actual bytes scanned.

```sql
-- External table (shows 0 bytes estimated)
SELECT COUNT(DISTINCT affiliated_base_number) 
FROM `ny_taxi_warehouse.yellow_trips_external`;

-- Native table (shows actual bytes)
SELECT COUNT(DISTINCT affiliated_base_number) 
FROM `ny_taxi_warehouse.yellow_trips`;
```

**Answer:** This demonstrates why external tables can't be used for cost estimation —
BigQuery doesn't know the data size until it reads from GCS.

---

## Question 3: How many records have both fare_amount = 0 and trip_distance = 0?

```sql
SELECT COUNT(*)
FROM `ny_taxi_warehouse.yellow_trips`
WHERE fare_amount = 0
  AND trip_distance = 0;
```

**Answer:** `~1,622`

These are likely cancelled trips or data entry errors — exactly the rows we filter
out in the Mage transformer block.

---

## Question 4: What is the best strategy for optimizing a table for filtering by pickup_datetime and ordering by VendorID?

**Answer:** `Partition by pickup_datetime, Cluster by VendorID`

```sql
CREATE OR REPLACE TABLE `ny_taxi_warehouse.yellow_trips_optimized`
PARTITION BY DATE(tpep_pickup_datetime)
CLUSTER BY VendorID
AS SELECT * FROM `ny_taxi_warehouse.yellow_trips_external`;
```

- **Partition by pickup_datetime** → filters on date only read relevant partitions
- **Cluster by VendorID** → within each partition, rows with same VendorID are co-located

---

## Question 5: Bytes processed — partitioned vs non-partitioned

```sql
-- Non-partitioned table
SELECT COUNT(*) AS trip_count
FROM `ny_taxi_warehouse.yellow_trips`
WHERE DATE(tpep_pickup_datetime) BETWEEN '2022-06-01' AND '2022-06-30';
-- Bytes processed: ~12.82 MB

-- Partitioned table
SELECT COUNT(*) AS trip_count
FROM `ny_taxi_warehouse.yellow_trips_partitioned`
WHERE DATE(tpep_pickup_datetime) BETWEEN '2022-06-01' AND '2022-06-30';
-- Bytes processed: ~1.12 MB
```

**Answer:** Non-partitioned ~12.82 MB vs Partitioned ~1.12 MB
→ Partitioned table uses ~11x less data — directly translating to lower cost.

---

## Question 6: Where is BigQuery data stored?

**Answer:** `GCP Bucket` (BigQuery's internal Colossus storage, separate from user GCS buckets)

BigQuery stores data in Google's internal distributed file system called **Colossus**,
in a columnar format called **Capacitor**. This is different from your GCS bucket — when
you load data from GCS into BigQuery, it gets copied into Colossus.

---

## Key Takeaways

1. **Always partition** time-series data by date — it's the single biggest cost optimization
2. **External tables** are great for exploration but don't use them in production pipelines
3. **Clustering** helps when you frequently filter on high-cardinality columns
4. **`SELECT *`** in BigQuery is expensive — always select only needed columns
5. BigQuery **caches** query results for 24 hours — identical queries within that window are free
