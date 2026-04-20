# Module 3: Data Warehouse with BigQuery

## Overview

Now that data is in our GCS data lake, we move it into **BigQuery** — GCP's fully managed,
serverless data warehouse — and learn how to make queries fast and cheap at scale.

---

## What I Learned

### What is a Data Warehouse?

A data warehouse is a system optimized for **analytical queries** (OLAP), not
transactional operations (OLTP like a web app database).

| | OLTP (PostgreSQL) | OLAP (BigQuery) |
|--|-------------------|----------------|
| **Use case** | App operations | Analytics / reporting |
| **Queries** | Many small reads/writes | Few large scans |
| **Scale** | GBs | TBs–PBs |
| **Speed** | Fast row lookups | Fast column scans |
| **Storage** | Row-oriented | Column-oriented |
| **Cost model** | Fixed server cost | Pay-per-query |

### BigQuery Internals

BigQuery is **columnar** — data is stored by column, not by row.

```
Row storage (Postgres):
[row1: col1, col2, col3] [row2: col1, col2, col3] ...

Column storage (BigQuery):
[col1: val1, val2, val3...] [col2: val1, val2, val3...] ...
```

When you run `SELECT total_amount FROM trips`, BigQuery only reads the `total_amount` column
— it skips all other columns entirely. On a table with 50 columns and 100M rows, this is
a massive performance win.

### Partitioning

Partitioning divides a table into segments by a column value. BigQuery only reads relevant
partitions when you filter on the partition column.

```sql
-- Create a partitioned table
CREATE OR REPLACE TABLE ny_taxi.yellow_trips_partitioned
PARTITION BY DATE(tpep_pickup_datetime)
AS SELECT * FROM ny_taxi.yellow_trips_external;
```

**Impact example:**
```
Unpartitioned table scan: 1.6 GB processed
Partitioned (filtered by date): 106 MB processed
→ 15x less data read = 15x cheaper query
```

### Clustering

Clustering sorts data within each partition by one or more columns. Useful when you 
frequently filter or group by those columns.

```sql
CREATE OR REPLACE TABLE ny_taxi.yellow_trips_partitioned_clustered
PARTITION BY DATE(tpep_pickup_datetime)
CLUSTER BY VendorID
AS SELECT * FROM ny_taxi.yellow_trips_external;
```

**When to use clustering:**
- Columns used frequently in `WHERE`, `GROUP BY`, `ORDER BY`
- High cardinality columns (many distinct values)
- After partitioning — clustering applies within each partition

### External Tables

BigQuery can query Parquet/CSV files directly from GCS **without** loading them first.
These are called **external tables**:

```sql
CREATE OR REPLACE EXTERNAL TABLE ny_taxi.yellow_trips_external
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://your-bucket/ny_taxi/yellow/*.parquet']
);
```

Trade-off: external tables are slower and more expensive per query than native tables,
but great for exploring raw data before committing to a schema.

---

## Tools Used

| Tool | Purpose |
|------|---------|
| BigQuery | Data warehouse — stores and queries structured data |
| GCS | Source of Parquet files for BigQuery |
| BigQuery Console | Web UI for running queries |
| `bq` CLI | Command-line tool for BigQuery operations |

---

## Folder Structure

```
03-data-warehouse/
├── README.md
├── queries/
│   ├── 01_create_external_table.sql    # Create external table from GCS
│   ├── 02_create_native_table.sql      # Load GCS → native BigQuery table
│   ├── 03_partitioning.sql             # Create partitioned tables
│   ├── 04_clustering.sql               # Create clustered tables
│   ├── 05_performance_comparison.sql   # Compare query costs
│   └── 06_analytics_queries.sql        # Business queries on taxi data
└── homework/
    └── homework_answers.md
```

---

## Key Commands

```bash
# List datasets in your project
bq ls

# List tables in a dataset
bq ls ny_taxi_warehouse

# Describe a table schema
bq show ny_taxi_warehouse.yellow_taxi_trips

# Run a query from CLI
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) FROM \`project.dataset.table\`"

# Load data from GCS
bq load \
  --source_format=PARQUET \
  ny_taxi_warehouse.yellow_taxi_trips \
  gs://bucket/path/*.parquet
```

---

## Cost Optimization Summary

| Strategy | Savings |
|----------|---------|
| Partition by date | Only scan relevant date ranges |
| Cluster by frequent filter columns | Reduce bytes within partitions |
| Use native tables over external | Faster + cheaper per query |
| `SELECT only needed columns` | Avoid `SELECT *` |
| Preview with `LIMIT` before full scan | Estimate cost before running |
| Cache results | BigQuery caches identical queries for 24h (free) |

---

## Resources

- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [BigQuery Pricing](https://cloud.google.com/bigquery/pricing)
- [Partitioned Tables Guide](https://cloud.google.com/bigquery/docs/partitioned-tables)
