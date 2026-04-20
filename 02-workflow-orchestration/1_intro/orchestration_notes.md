# Workflow Orchestration — Concepts & Notes

## Why Orchestration?

A data pipeline is a sequence of steps that moves data from source to destination. In small projects,
you can run scripts manually. But in production, pipelines need to be:

- **Scheduled** — run at 2am every day automatically
- **Monitored** — know immediately when a step fails
- **Retried** — automatically retry failed steps (transient errors are common)
- **Ordered** — step B must not run until step A succeeds
- **Logged** — keep a history of every run for debugging

An **orchestrator** manages all of this for you.

---

## Popular Orchestration Tools

| Tool | Notes |
|------|-------|
| **Apache Airflow** | Industry standard, widely used, but complex to set up |
| **Mage.AI** | Modern, simpler, great UI, used in this course |
| **Prefect** | Python-native, great for Python teams |
| **Kestra** | YAML-based, very declarative |
| **Dagster** | Asset-based thinking, strong typing |
| **Luigi** | Older, simpler, less popular now |

This course uses **Mage.AI** because it's developer-friendly and has excellent GCP integrations.

---

## DAGs — Directed Acyclic Graphs

Every orchestration tool represents pipelines as a **DAG**:

```
     ┌──────────────┐
     │  Data Loader │   ← downloads raw data
     └──────┬───────┘
            │
     ┌──────▼───────┐
     │  Transformer │   ← cleans and enriches data
     └──────┬───────┘
            │
     ┌──────▼───────┐
     │  GCS Export  │   ← writes to data lake
     └──────┬───────┘
            │
     ┌──────▼───────┐
     │  BQ Loader   │   ← loads into data warehouse
     └──────────────┘
```

**Why Acyclic?** — no circular dependencies. If task A depends on B which depends on A, 
you'd have an infinite loop. DAGs prevent this.

---

## Mage.AI Architecture

Mage organizes work into **Blocks** and **Pipelines**:

### Blocks
A block is a single unit of work — typically a Python function. Types:
- **Data Loader** — fetches data (API, file, database)
- **Transformer** — cleans, filters, enriches data
- **Data Exporter** — writes to a destination (GCS, BigQuery, Postgres)

Blocks are **reusable** across pipelines.

### Pipelines
A pipeline chains blocks together. Mage figures out the order from dependencies.

### Triggers
Pipelines run via:
- **Schedule** — cron-like ("run every day at midnight")
- **Event** — triggered by an external event (new file in GCS)
- **API** — triggered by an HTTP call
- **Manual** — click Run in the UI

---

## The ETL vs ELT Distinction

Traditional pipelines use **ETL**: Extract → Transform → Load
Modern cloud pipelines use **ELT**: Extract → Load → Transform

| | ETL | ELT |
|--|-----|-----|
| **When** | Pre-cloud era | Cloud data warehouse era |
| **Transform location** | Before loading | After loading (in BigQuery/Snowflake) |
| **Why ELT now?** | Storage is cheap; compute in cloud is powerful |
| **Tool** | Custom scripts | dbt (Module 4) |

In this module we do a light ETL: transform basic issues (data types, column names) 
before loading to GCS. Heavy transformations happen later in dbt.

---

## Data Lake vs Data Warehouse (revisited)

```
Raw Sources → [Extract] → Data Lake (GCS) → [Transform] → Data Warehouse (BigQuery)
                                                                     ↓
                                                              BI Tools / Dashboards
```

**Data Lake (GCS)**
- Store raw, unprocessed data
- Schema is flexible — files can be CSV, Parquet, JSON
- Cheap storage — keep everything "just in case"
- Processed by Spark or loaded into BigQuery later

**Data Warehouse (BigQuery)**
- Structured, optimized for SQL queries
- Enforces schema
- Pay-per-query model
- Used by analysts and BI tools

---

## Partitioning Strategy

When writing data to GCS, always partition by the most common filter column.
For time-series data (like taxi trips), partition by year/month:

```
gs://bucket/yellow_taxi/
├── year=2021/month=01/data.parquet   → 1.2M rows
├── year=2021/month=02/data.parquet   → 1.1M rows
└── year=2021/month=03/data.parquet   → 1.3M rows
```

**Why it matters:** When a query filters `WHERE month = '2021-01'`, BigQuery only reads
`month=01/` partition — skipping 2/3 of the data entirely. For large datasets this is
the difference between a $0.001 query and a $5 query.

---

## Error Handling in Pipelines

Real pipelines fail. Common causes:
- API rate limits / timeouts
- Network blips
- Source data format changes
- Out-of-memory on large files
- GCS permission errors

Mage handles this with:
- **Retries** — automatically retry failed blocks N times with exponential backoff
- **Callbacks** — run a "on_failure" block when something breaks
- **Alerts** — send Slack/email notification on failure
- **Status tracking** — every run stored with status, logs, and output metadata
