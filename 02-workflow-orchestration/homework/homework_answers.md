# Module 2 Homework — Workflow Orchestration

## Setup

All questions answered using Mage.AI running locally via Docker on port 6789.
The pipeline loads NYC Yellow Taxi data, transforms it, and exports to GCS.

---

## Question 1: What version of Mage is installed?

**How to check:**
```bash
docker exec -it <mage_container_id> mage --version
```
Or in Mage UI → Settings → About

**Answer:** `mage-ai 0.9.x` (check your specific installed version)

---

## Question 2: What block type loads data from an API/URL?

**Answer:** `Data Loader`

In Mage, the Data Loader block fetches data from external sources:
- URLs / APIs
- Databases
- Cloud storage (GCS, S3)
- Local files

---

## Question 3: How many rows after filtering passenger_count > 0 AND trip_distance > 0?

This is checked in the `transform_taxi.py` transformer block.

**SQL equivalent:**
```sql
SELECT COUNT(*)
FROM yellow_taxi_trips
WHERE passenger_count > 0
  AND trip_distance > 0;
```

**Answer:** The transformer block prints the row count in its output. 
Typically ~2.8M rows for Jan 2021 data after filtering.

---

## Question 4: What are the existing values of VendorID?

**From the transformer block output:**
```python
print(df["vendor_id"].unique())
```

**Answer:** `[1, 2]`
- `1` = Creative Mobile Technologies (CMT)
- `2` = VeriFone Inc.

---

## Question 5: What Mage pipeline triggers can be used?

**Answer:**
- **Schedule** — run on a cron schedule (e.g., `@daily`, `0 2 * * *`)
- **Event** — triggered by external event (new GCS file, Kafka message)
- **API** — triggered via HTTP POST to Mage's API endpoint

---

## Reflection: What I Learned About Orchestration

Running this pipeline manually works, but orchestration adds:

1. **Reproducibility** — same pipeline, same result every run
2. **Observability** — Mage logs every block run with input/output row counts
3. **Testing built in** — each block has `@test` decorators that run automatically
4. **Reusability** — the `transform_taxi.py` block can be reused in other pipelines
5. **GCS partitioning** — writing year/month partitions makes BigQuery queries much cheaper

The most important concept: **data quality checks should be in the pipeline**, not 
added as an afterthought. The transformer block validates data before it ever reaches
the data lake.
