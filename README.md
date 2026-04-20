# Data Engineering Zoomcamp — My Learning Journey

[![DataTalksClub](https://img.shields.io/badge/DataTalksClub-DE%20Zoomcamp-blue)](https://github.com/DataTalksClub/data-engineering-zoomcamp)

This repository documents my progress through the [DataTalksClub Data Engineering Zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp) — a free 9-week course on building production-ready data pipelines.

---

## What I'm Building

Throughout this course, I'm learning how to design, build, and operate end-to-end data pipelines using industry-standard tools. The final outcome is a production-grade data pipeline with:

- Infrastructure provisioned with **Terraform** on **GCP**
- Data ingested and stored in a **data lake (GCS)**
- Data transformed and loaded into a **data warehouse (BigQuery)**
- Analytics models built with **dbt**
- Orchestrated with a workflow tool
- Processed at scale with **Apache Spark**
- Streamed in real time with **Kafka**

---

## Course Modules

| # | Module | Topics | Status |
|---|--------|---------|--------|
| 1 | [Containerization & IaC](./01-docker-terraform/) | Docker, PostgreSQL, Terraform, GCP | ✅ Complete |
| 2 | [Workflow Orchestration](./02-workflow-orchestration/) | Mage.AI, GCS pipelines, DAGs | ✅ Complete |
| 3 | [Data Warehouse](./03-data-warehouse/) | BigQuery, partitioning, clustering | ✅ Complete |
| 4 | [Analytics Engineering](./04-analytics-engineering/) | dbt, data modeling, BI tools | ✅ Complete |
| 5 | [Batch Processing](./05-batch-processing/) | Apache Spark, PySpark, Spark SQL | ✅ Complete |
| 6 | [Stream Processing](./06-stream-processing/) | Kafka, producers, consumers | ✅ Complete |
| — | [Capstone Project](./capstone-project/) | End-to-end NYC taxi pipeline | ✅ Complete |

---

## Tech Stack

```
Cloud:          Google Cloud Platform (GCP)
IaC:            Terraform
Containers:     Docker, docker-compose
Database:       PostgreSQL (local), BigQuery (cloud)
Orchestration:  Mage.AI / Kestra
Transform:      dbt (data build tool)
Batch:          Apache Spark (PySpark)
Streaming:      Apache Kafka
Language:       Python, SQL
```

---

## How to Use This Repo

Each module folder contains:
- `README.md` — concepts explained in my own words, setup instructions, key learnings
- Working code (scripts, configs, queries)
- Homework solutions with the SQL queries I wrote

Clone the repo and follow the README in each module folder to reproduce the work.

```bash
git clone https://github.com/DayDay0308/data-engineering-zoomcamp.git
cd data-engineering-zoomcamp
```

**Prerequisites:** Docker Desktop, Python 3.11+, GCP account, Terraform 1.7+

---

## Key Concepts Learned

- **Containerization** with Docker — reproducible environments for data tools
- **Infrastructure as Code** with Terraform — provision cloud resources like GCS and BigQuery programmatically
- **Data Lakes vs Data Warehouses** — when to use each and how they fit in a pipeline
- **Batch data ingestion** — efficiently loading large datasets into Postgres and GCS
- **SQL analytics** on NYC taxi trip data — aggregations, joins, window functions

---

## Resources

- [DataTalksClub DE Zoomcamp GitHub](https://github.com/DataTalksClub/data-engineering-zoomcamp)
- [Course Slack Community](https://datatalks.club/slack.html)
- [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
