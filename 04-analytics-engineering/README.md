# Module 4: Analytics Engineering with dbt

## Overview

We have raw taxi data in BigQuery. Now we need to **transform it into clean, reliable,
well-documented models** that analysts can actually trust and use. That's what **dbt** does.

Analytics engineering sits at the intersection of data engineering and data analysis.
dbt is the tool of choice because it brings software engineering best practices
(version control, testing, documentation) to SQL transformations.

---

## What I Learned

### What is dbt?

**dbt** (data build tool) lets you transform data in your warehouse using SQL.

```
Raw data in BigQuery
        ↓
    dbt models (SQL files)
        ↓
Clean, tested, documented tables in BigQuery
        ↓
    BI Tools (Looker, Metabase, Tableau)
```

Key insight: dbt **only transforms** data. It doesn't extract or load — it expects
data to already be in your warehouse (from Mage/Spark/etc).

### Why Not Just Write SQL?

| Raw SQL | dbt |
|---------|-----|
| Files scattered everywhere | Organized project structure |
| No testing | Built-in data tests |
| No documentation | Auto-generated docs site |
| Manual dependency management | Automatic DAG from `ref()` |
| Hard to reuse logic | Macros (reusable SQL functions) |

### dbt Models

A **model** is a `.sql` file that defines a SELECT statement. dbt compiles it
and runs it as `CREATE TABLE` or `CREATE VIEW` in BigQuery.

```sql
-- models/staging/stg_yellow_taxi.sql
SELECT
    vendorid AS vendor_id,
    tpep_pickup_datetime AS pickup_datetime,
    tpep_dropoff_datetime AS dropoff_datetime,
    passenger_count,
    trip_distance,
    total_amount
FROM {{ source('staging', 'yellow_trips') }}   -- ← dbt source reference
WHERE passenger_count > 0
  AND trip_distance > 0
```

### Model Layers

We organize models into layers:

```
Raw (BigQuery) → Staging → Core → Marts
```

| Layer | Folder | Purpose |
|-------|--------|---------|
| **Staging** | `models/staging/` | Clean and rename raw columns. 1:1 with source tables |
| **Core** | `models/core/` | Join staging models, business logic |
| **Marts** | `models/marts/` | Final tables for specific use cases (finance, ops) |

### The `ref()` Function

`ref()` creates dependencies between models. dbt builds a DAG automatically:

```sql
-- models/core/fact_trips.sql
SELECT
    t.vendor_id,
    t.pickup_datetime,
    z.zone AS pickup_zone,
    t.total_amount
FROM {{ ref('stg_yellow_taxi') }} t           -- ← depends on staging model
LEFT JOIN {{ ref('dim_zones') }} z            -- ← depends on zones dimension
    ON t.pickup_location_id = z.location_id
```

### dbt Testing

dbt has built-in test types:

```yaml
# schema.yml
models:
  - name: stg_yellow_taxi
    columns:
      - name: trip_id
        tests:
          - unique          # no duplicate trip IDs
          - not_null        # no missing values
      - name: vendor_id
        tests:
          - accepted_values:
              values: [1, 2]  # only valid vendors
```

Run with: `dbt test`

---

## Folder Structure

```
04-analytics-engineering/
├── README.md
└── dbt_taxi/
    ├── dbt_project.yml          # Project configuration
    ├── profiles.yml             # BigQuery connection config
    ├── models/
    │   ├── staging/
    │   │   ├── schema.yml       # Source definitions + tests
    │   │   ├── stg_yellow_taxi.sql
    │   │   └── stg_green_taxi.sql
    │   └── core/
    │       ├── schema.yml
    │       ├── fact_trips.sql   # Main fact table (yellow + green combined)
    │       └── dim_zones.sql    # Zone dimension table
    ├── seeds/
    │   └── taxi_zone_lookup.csv # Static lookup data loaded with dbt seed
    ├── macros/
    │   └── get_payment_type_description.sql
    └── tests/
        └── assert_positive_total_amount.sql
```

---

## How to Run

```bash
cd dbt_taxi

# Install dbt
pip install dbt-bigquery

# Test connection to BigQuery
dbt debug

# Seed static lookup tables (zone names)
dbt seed

# Run all models
dbt run

# Run tests
dbt test

# Generate and serve documentation
dbt docs generate
dbt docs serve    # Opens at http://localhost:8080

# Run everything in order
dbt build
```

---

## Resources

- [dbt Documentation](https://docs.getdbt.com/)
- [dbt BigQuery Setup](https://docs.getdbt.com/docs/core/connect-data-platform/bigquery-setup)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
