# Capstone Project: NYC Taxi Analytics Pipeline

## Project Summary

An end-to-end data engineering pipeline that ingests, transforms, and visualizes
NYC Yellow Taxi trip data — applying every concept learned in the DE Zoomcamp.

**Dataset:** NYC TLC Yellow Taxi Trip Records (2021–2022)
**Source:** [NYC TLC Open Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE (Terraform)                  │
│                   GCS Bucket + BigQuery Dataset                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────┐
│                  INGESTION (Mage.AI Pipeline)                   │
│                                                                 │
│  NYC TLC API ──► Data Loader ──► Transformer ──► GCS Exporter  │
│                                                                 │
│  Output: gs://bucket/yellow_taxi/year=*/month=*/*.parquet       │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────┐
│               DATA WAREHOUSE (BigQuery)                         │
│                                                                 │
│  External Table (GCS)                                           │
│       ↓                                                         │
│  Partitioned Native Table (by day, clustered by vendor)         │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────┐
│              TRANSFORMATION (dbt)                               │
│                                                                 │
│  stg_yellow_taxi ──┐                                            │
│                    ├──► fact_trips ──► dim_zones               │
│  stg_zones ────────┘                                            │
│                                                                 │
│  Tests: unique, not_null, accepted_values on all key columns    │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────┐
│                 DASHBOARD (Looker Studio / Metabase)            │
│                                                                 │
│  • Monthly trips & revenue trend                                │
│  • Peak hours heatmap                                           │
│  • Top pickup/dropoff zones map                                 │
│  • Revenue by payment type                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technologies Used

| Layer | Tool | Purpose |
|-------|------|---------|
| Infrastructure | Terraform | Provision GCS + BigQuery |
| Containerization | Docker | Run Mage locally |
| Orchestration | Mage.AI | Scheduled pipeline |
| Data Lake | Google Cloud Storage | Raw Parquet storage |
| Data Warehouse | BigQuery | Analytical queries |
| Transformation | dbt | SQL models + tests |
| Dashboard | Looker Studio | Visualization |
| Language | Python, SQL | Scripting and queries |

---

## Pipeline Steps

### Step 1: Provision Infrastructure

```bash
cd terraform
terraform init
terraform apply
# Creates: GCS bucket + BigQuery dataset
```

### Step 2: Run Ingestion Pipeline (Mage)

```bash
cd mage_pipeline
docker-compose up -d
# Open http://localhost:6789
# Run pipeline: ny_taxi_ingestion
# Loads Jan 2021–Jun 2022 → GCS
```

### Step 3: Create BigQuery Tables

```sql
-- External table over GCS
CREATE OR REPLACE EXTERNAL TABLE `ny_taxi.yellow_trips_external`
OPTIONS (format='PARQUET', uris=['gs://YOUR_BUCKET/yellow_taxi/**/*.parquet']);

-- Native partitioned table
CREATE OR REPLACE TABLE `ny_taxi.yellow_trips`
PARTITION BY DATE(tpep_pickup_datetime)
CLUSTER BY VendorID
AS SELECT * FROM `ny_taxi.yellow_trips_external`;
```

### Step 4: Run dbt Transformations

```bash
cd dbt
dbt deps
dbt seed
dbt run
dbt test
dbt docs generate && dbt docs serve
```

### Step 5: Connect Dashboard

Connect Looker Studio to BigQuery dataset `ny_taxi`:
- Source table: `fact_trips`
- Build charts using the pre-built queries in `dashboard/queries.sql`

---

## Dashboard Metrics

The final dashboard answers these business questions:

1. **How has taxi usage changed month-over-month?**
   - Line chart: trips per month, revenue per month

2. **When is demand highest?**
   - Heatmap: trips by hour of day × day of week

3. **Where do most trips start and end?**
   - Bar chart: top 10 pickup zones, top 10 dropoff zones

4. **What's the revenue split between credit card and cash?**
   - Pie chart: payment type breakdown

5. **How do the two vendors compare?**
   - Side-by-side: Vendor 1 vs Vendor 2 — trips, avg fare, avg distance

---

## Data Quality

dbt tests run on every pipeline execution:

| Test | Column | Result |
|------|--------|--------|
| `unique` | `trip_id` | ✅ No duplicates |
| `not_null` | `vendor_id`, `pickup_datetime`, `total_amount` | ✅ |
| `accepted_values` | `vendor_id` in [1,2] | ✅ |
| `accepted_values` | `payment_type` description | ✅ |
| Custom: `assert_positive_total` | `total_amount > 0` | ✅ |

---

## Results / Findings

After running the full pipeline on 18 months of NYC taxi data (2021-01 to 2022-06):

- **Total trips processed:** ~43 million
- **Total revenue:** ~$615 million
- **Peak pickup hour:** 6 PM (18:00)
- **Busiest zone:** Midtown Center
- **Most common payment:** Credit Card (68%)
- **Avg trip distance:** 3.1 miles
- **Avg fare:** $14.20

---

## Reproducibility

Anyone can reproduce this pipeline with:

```bash
git clone https://github.com/DayDay0308/data-engineering-zoomcamp.git
cd capstone-project

# 1. Set your GCP project
export GCP_PROJECT_ID="your-project-id"

# 2. Authenticate
gcloud auth application-default login

# 3. Provision infra
cd terraform && terraform apply

# 4. Start Mage and run ingestion
cd ../mage_pipeline && docker-compose up -d

# 5. Run dbt
cd ../dbt && dbt build
```

---

## Key Learnings

This capstone tied together every module:

- **Module 1** — Docker/Terraform gave us the infrastructure foundation
- **Module 2** — Mage made the pipeline automated and observable
- **Module 3** — BigQuery partitioning made analytics queries 10x cheaper
- **Module 4** — dbt gave us tested, documented, reusable SQL models
- **Module 5** — Spark principles helped understand columnar processing
- **Module 6** — Kafka showed how this pipeline could be extended to real-time

The hardest part wasn't any single tool — it was understanding how they connect.
A data engineer's job is to build reliable data systems that downstream teams can trust.
Testing (dbt tests), documentation (dbt docs), and observability (Mage logs) are
what separates a production pipeline from a script that works once.
