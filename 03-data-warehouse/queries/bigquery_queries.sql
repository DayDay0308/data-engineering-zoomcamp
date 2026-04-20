-- ============================================================
-- 01: Create External Table from GCS
-- ============================================================
-- This queries Parquet files directly in GCS without loading.
-- Great for exploration; slower and pricier for production.

CREATE OR REPLACE EXTERNAL TABLE `ny_taxi_warehouse.yellow_trips_external`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://YOUR_BUCKET/ny_taxi/yellow/*.parquet']
);

-- Quick check
SELECT COUNT(*) FROM `ny_taxi_warehouse.yellow_trips_external`;
SELECT * FROM `ny_taxi_warehouse.yellow_trips_external` LIMIT 5;


-- ============================================================
-- 02: Create Native BigQuery Table from External
-- ============================================================
-- This physically copies data into BigQuery storage.
-- Faster queries, and BigQuery can collect statistics for optimization.

CREATE OR REPLACE TABLE `ny_taxi_warehouse.yellow_trips`
AS SELECT * FROM `ny_taxi_warehouse.yellow_trips_external`;

-- Compare row counts
SELECT 
  'external' AS table_type, COUNT(*) AS row_count 
  FROM `ny_taxi_warehouse.yellow_trips_external`
UNION ALL
SELECT 
  'native' AS table_type, COUNT(*) AS row_count 
  FROM `ny_taxi_warehouse.yellow_trips`;


-- ============================================================
-- 03: Partitioned Table
-- ============================================================
-- Partition by pickup date — queries filtering by date only scan
-- the relevant partitions instead of the whole table.

CREATE OR REPLACE TABLE `ny_taxi_warehouse.yellow_trips_partitioned`
PARTITION BY DATE(tpep_pickup_datetime)
AS
SELECT * FROM `ny_taxi_warehouse.yellow_trips_external`;

-- Check partition info
SELECT
  table_name,
  partition_id,
  total_rows,
  total_logical_bytes / POW(1024, 2) AS size_mb
FROM `ny_taxi_warehouse.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'yellow_trips_partitioned'
ORDER BY partition_id
LIMIT 20;


-- ============================================================
-- 04: Clustered + Partitioned Table
-- ============================================================
-- Adds clustering on top of partitioning.
-- Within each date partition, rows are sorted by VendorID.

CREATE OR REPLACE TABLE `ny_taxi_warehouse.yellow_trips_partitioned_clustered`
PARTITION BY DATE(tpep_pickup_datetime)
CLUSTER BY VendorID
AS
SELECT * FROM `ny_taxi_warehouse.yellow_trips_external`;


-- ============================================================
-- 05: Performance Comparison
-- ============================================================
-- Run these and compare the "bytes processed" in BigQuery UI

-- NON-partitioned: scans entire table
SELECT COUNT(*) 
FROM `ny_taxi_warehouse.yellow_trips`
WHERE DATE(tpep_pickup_datetime) = '2021-01-15';

-- PARTITIONED: only reads the 2021-01-15 partition
SELECT COUNT(*) 
FROM `ny_taxi_warehouse.yellow_trips_partitioned`
WHERE DATE(tpep_pickup_datetime) = '2021-01-15';

-- NON-clustered: scans all rows in date range
SELECT COUNT(*)
FROM `ny_taxi_warehouse.yellow_trips_partitioned`
WHERE DATE(tpep_pickup_datetime) BETWEEN '2021-01-01' AND '2021-03-31'
  AND VendorID = 1;

-- CLUSTERED: within each partition, only reads VendorID=1 rows
SELECT COUNT(*)
FROM `ny_taxi_warehouse.yellow_trips_partitioned_clustered`
WHERE DATE(tpep_pickup_datetime) BETWEEN '2021-01-01' AND '2021-03-31'
  AND VendorID = 1;


-- ============================================================
-- 06: Analytics Queries
-- ============================================================

-- Total trips and revenue by month
SELECT
  DATE_TRUNC(tpep_pickup_datetime, MONTH) AS month,
  COUNT(*) AS total_trips,
  ROUND(SUM(total_amount), 2) AS total_revenue,
  ROUND(AVG(total_amount), 2) AS avg_fare,
  ROUND(AVG(trip_distance), 2) AS avg_distance
FROM `ny_taxi_warehouse.yellow_trips_partitioned`
GROUP BY month
ORDER BY month;


-- Peak hours — when are most trips taken?
SELECT
  EXTRACT(HOUR FROM tpep_pickup_datetime) AS hour_of_day,
  COUNT(*) AS trip_count,
  ROUND(AVG(total_amount), 2) AS avg_fare
FROM `ny_taxi_warehouse.yellow_trips_partitioned`
GROUP BY hour_of_day
ORDER BY trip_count DESC;


-- Top 10 pickup-dropoff pairs (need zone lookup table)
SELECT
  PULocationID AS pickup_zone,
  DOLocationID AS dropoff_zone,
  COUNT(*) AS trip_count,
  ROUND(AVG(total_amount), 2) AS avg_fare
FROM `ny_taxi_warehouse.yellow_trips_partitioned`
GROUP BY pickup_zone, dropoff_zone
ORDER BY trip_count DESC
LIMIT 10;


-- Revenue by payment type
SELECT
  CASE payment_type
    WHEN 1 THEN 'Credit Card'
    WHEN 2 THEN 'Cash'
    WHEN 3 THEN 'No Charge'
    WHEN 4 THEN 'Dispute'
    ELSE 'Unknown'
  END AS payment_method,
  COUNT(*) AS trips,
  ROUND(SUM(total_amount), 2) AS total_revenue,
  ROUND(AVG(tip_amount), 2) AS avg_tip
FROM `ny_taxi_warehouse.yellow_trips_partitioned`
GROUP BY payment_type
ORDER BY trips DESC;
