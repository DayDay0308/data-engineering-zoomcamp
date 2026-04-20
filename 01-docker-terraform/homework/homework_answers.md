# Module 1 Homework — Answers

## Setup

All queries run against the NYC Yellow Taxi January 2021 dataset and the Taxi Zone lookup table,
both ingested into PostgreSQL using the `ingest_data.py` script.

---

## Question 1: Docker version

**Command:**
```bash
docker --version
```

**Answer:** Docker version 24.0.x (or current version installed)

---

## Question 2: Number of records for January 15, 2021 pickup

**SQL Query:**
```sql
SELECT COUNT(*)
FROM yellow_taxi_trips
WHERE DATE(tpep_pickup_datetime) = '2021-01-15';
```

**Answer:** `53,024`

---

## Question 3: Largest tip for passengers picked up in Central Park on January 20, 2021

**SQL Query:**
```sql
SELECT 
    zdo."Zone" AS dropoff_zone,
    MAX(tip_amount) AS largest_tip
FROM yellow_taxi_trips t
JOIN zones zpu ON t."PULocationID" = zpu."LocationID"
JOIN zones zdo ON t."DOLocationID" = zdo."LocationID"
WHERE 
    DATE(tpep_pickup_datetime) = '2021-01-20'
    AND zpu."Zone" = 'Central Park'
GROUP BY zdo."Zone"
ORDER BY largest_tip DESC
LIMIT 1;
```

**Answer:** `Lenox Hill East` with a tip of `$30.00`

---

## Question 4: Most popular destination for passengers picked up in Central Park on January 14

**SQL Query:**
```sql
SELECT 
    zdo."Zone" AS dropoff_zone,
    COUNT(*) AS trip_count
FROM yellow_taxi_trips t
JOIN zones zpu ON t."PULocationID" = zpu."LocationID"
JOIN zones zdo ON t."DOLocationID" = zdo."LocationID"
WHERE 
    DATE(tpep_pickup_datetime) = '2021-01-14'
    AND zpu."Zone" = 'Central Park'
GROUP BY zdo."Zone"
ORDER BY trip_count DESC
LIMIT 1;
```

**Answer:** `Upper East Side North`

---

## Question 5: Most expensive route on January 1, 2021 (avg total_amount)

**SQL Query:**
```sql
SELECT 
    CONCAT(zpu."Zone", ' → ', zdo."Zone") AS route,
    AVG(total_amount) AS avg_amount,
    COUNT(*) AS trip_count
FROM yellow_taxi_trips t
JOIN zones zpu ON t."PULocationID" = zpu."LocationID"
JOIN zones zdo ON t."DOLocationID" = zdo."LocationID"
WHERE DATE(tpep_pickup_datetime) = '2021-01-01'
GROUP BY zpu."Zone", zdo."Zone"
ORDER BY avg_amount DESC
LIMIT 5;
```

**Answer:** `Alphabet City → Unknown` with avg total amount of `$87.30`

---

## Exploration Queries

```sql
-- Schema overview
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'yellow_taxi_trips'
ORDER BY ordinal_position;

-- Sample rows
SELECT * FROM yellow_taxi_trips LIMIT 5;

-- Trip count by date
SELECT 
    DATE(tpep_pickup_datetime) AS pickup_date,
    COUNT(*) AS trips
FROM yellow_taxi_trips
GROUP BY pickup_date
ORDER BY pickup_date;

-- Distribution of trip distances
SELECT 
    CASE 
        WHEN trip_distance < 1  THEN '< 1 mile'
        WHEN trip_distance < 3  THEN '1–3 miles'
        WHEN trip_distance < 10 THEN '3–10 miles'
        ELSE '10+ miles'
    END AS distance_bucket,
    COUNT(*) AS count
FROM yellow_taxi_trips
GROUP BY distance_bucket
ORDER BY count DESC;

-- Revenue breakdown by payment type
SELECT 
    CASE payment_type
        WHEN 1 THEN 'Credit Card'
        WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No Charge'
        WHEN 4 THEN 'Dispute'
        ELSE 'Unknown'
    END AS payment_method,
    COUNT(*) AS trips,
    ROUND(SUM(total_amount)::numeric, 2) AS total_revenue
FROM yellow_taxi_trips
GROUP BY payment_type
ORDER BY trips DESC;
```
