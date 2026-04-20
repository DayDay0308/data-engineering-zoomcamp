# Module 2: Workflow Orchestration

## Overview

In Module 1 we ran our ingestion script manually. That doesn't scale — real pipelines need to:
- Run **automatically** on a schedule
- **Retry** when something fails
- **Alert** when there's a problem
- Be **monitored** with logs and status dashboards

That's what workflow orchestration solves. This module uses **Mage.AI** (and introduces Kestra) to turn our one-off script into a production pipeline.

---

## What I Learned

### The Problem with Manual Scripts

Running `python ingest_data.py` works once, but in production you need:

| Requirement | Without Orchestration | With Orchestration |
|-------------|----------------------|--------------------|
| Scheduling | Manual / cron | Trigger-based or scheduled |
| Failure handling | Script crashes, nothing happens | Auto-retry with alerts |
| Visibility | Check terminal output | Dashboard with run history |
| Dependencies | Run scripts in correct order manually | DAG manages order |
| Reproducibility | Hard — environment varies | Containerized, consistent |

### What is a DAG?

A **DAG** (Directed Acyclic Graph) is how orchestration tools model pipelines:

```
Extract → Transform → Load
   ↓           ↓         ↓
(fetch    (clean,     (write to
 data)    validate)    GCS/BQ)
```

- **Directed** = tasks have a defined order
- **Acyclic** = no circular dependencies (no loops)
- **Graph** = a network of connected tasks

### Mage.AI

Mage is a modern orchestration tool that replaced older, more complex tools like Airflow for many teams. Key features:

- **Block-based pipelines** — each step is a reusable "block" (data loader, transformer, exporter)
- **Built-in UI** — visualize and trigger pipelines from a browser
- **Native Python** — write standard Python, no special decorators needed
- **Docker-native** — runs as a container

### Pipeline Architecture (Module 2)

```
NYC Taxi API / URL
        ↓
  [Data Loader]         ← Mage block: fetch parquet from URL
        ↓
  [Transformer]         ← Mage block: clean columns, fix dtypes, add derived columns
        ↓
  [GCS Exporter]        ← Mage block: write partitioned parquet to GCS data lake
        ↓
  [BQ Loader]           ← Mage block: load from GCS into BigQuery
```

---

## Tools Used

| Tool | Purpose |
|------|---------|
| Mage.AI | Pipeline orchestration |
| Google Cloud Storage | Data lake destination |
| BigQuery | Data warehouse destination |
| Docker | Run Mage in a container |
| Python / pandas | Data transformation |
| pyarrow | Parquet file handling |

---

## Folder Structure

```
02-workflow-orchestration/
├── 1_intro/
│   └── orchestration_notes.md   # Concepts: DAGs, orchestration, why it matters
├── 2_mage_pipeline/
│   ├── docker-compose.yml       # Run Mage.AI locally
│   ├── blocks/
│   │   ├── load_taxi_data.py    # Data Loader block
│   │   ├── transform_taxi.py    # Transformer block
│   │   └── export_to_gcs.py    # GCS Exporter block
│   └── pipeline_notes.md
├── 3_gcs_pipeline/
│   ├── blocks/
│   │   ├── load_from_gcs.py    # Load from data lake
│   │   └── export_to_bigquery.py  # Write to data warehouse
│   └── gcs_to_bq_notes.md
└── homework/
    └── homework_answers.md
```

---

## How to Run Mage Locally

### Start Mage with Docker

```bash
cd 2_mage_pipeline

# Start Mage
docker-compose up -d

# Open the UI
open http://localhost:6789
```

### Create a Pipeline in the UI

1. Click **New Pipeline** → choose **Standard (batch)**
2. Name it `ny_taxi_ingestion`
3. Add blocks in order: Data Loader → Transformer → Data Exporter
4. Paste the code from the `blocks/` folder into each block
5. Click **Run Pipeline**

### Run with GCP Credentials

Before the GCS exporter works, set your credentials:

```bash
# In docker-compose.yml, set:
environment:
  GOOGLE_SERVICE_ACC_KEY_FILEPATH: /home/src/service-account.json

# Mount your key:
volumes:
  - /path/to/your/service-account.json:/home/src/service-account.json
```

---

## Key Concepts: Partitioning

When writing to GCS, we **partition** data by date so queries only scan relevant files:

```
gs://my-bucket/ny_taxi/yellow/
├── year=2021/
│   ├── month=01/
│   │   └── part.0.parquet
│   ├── month=02/
│   │   └── part.0.parquet
...
```

Instead of one giant file, each partition is a smaller file. BigQuery and Spark can skip entire partitions when filtering by date — massive performance gains.

```python
# pyarrow partition writing
import pyarrow as pa
import pyarrow.parquet as pq

pq.write_to_dataset(
    table,
    root_path="gs://bucket/ny_taxi/",
    partition_cols=["year", "month"],
)
```

---

## Resources

- [Mage.AI Documentation](https://docs.mage.ai/)
- [Mage Quickstart with Docker](https://docs.mage.ai/getting-started/setup)
- [GCS Python Client](https://cloud.google.com/storage/docs/reference/libraries#client-libraries-install-python)
