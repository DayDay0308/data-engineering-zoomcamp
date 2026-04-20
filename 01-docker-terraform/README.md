# Module 1: Containerization & Infrastructure as Code

## Overview

This module covers the foundational infrastructure skills every data engineer needs before building pipelines. We learn how to:

- **Containerize** data tools using Docker so they run consistently anywhere
- **Ingest data** into PostgreSQL using Python
- **Provision cloud infrastructure** on GCP using Terraform (Infrastructure as Code)

---

## What I Learned

### 🐳 Docker & Containers

Docker solves the classic *"it works on my machine"* problem. Instead of installing tools directly on your OS, you package the tool + its dependencies into a **container image**. Anyone can run that image and get identical behavior.

Key concepts:
- **Image** — a blueprint/snapshot of a filesystem (e.g., `postgres:13`)
- **Container** — a running instance of an image
- **Dockerfile** — instructions to build a custom image
- **docker-compose** — tool to define and run multi-container apps together

### 🗄️ PostgreSQL + pgAdmin

For this module we run PostgreSQL (database) and pgAdmin (GUI client) as Docker containers that talk to each other over a shared **Docker network**.

### 🐍 Data Ingestion with Python

We use Python + SQLAlchemy to ingest the NYC Taxi trip data (a classic DE dataset) into PostgreSQL. The script:
1. Downloads the CSV/parquet file
2. Chunks it into batches (to handle large files)
3. Inserts each batch into Postgres using pandas + SQLAlchemy

### 🌍 Terraform — Infrastructure as Code (IaC)

Instead of clicking around the GCP console, we define our cloud infrastructure in `.tf` files and let Terraform create/destroy it automatically.

Why IaC matters:
- **Reproducible** — same config = same infrastructure every time
- **Version controlled** — track changes in Git like code
- **Destroyable** — `terraform destroy` cleans up everything (no surprise bills!)

For this module we provision:
- A **GCS bucket** (Google Cloud Storage) — our data lake
- A **BigQuery dataset** — our data warehouse

---

## Tools Used

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | 24+ | Containerization |
| PostgreSQL | 13 | Local database |
| pgAdmin | 4 | Database GUI |
| Python | 3.11 | Data ingestion scripts |
| pandas | 2.x | Data manipulation |
| SQLAlchemy | 2.x | DB connection |
| Terraform | 1.7+ | Infrastructure as Code |
| GCP | - | Cloud provider |

---

## Folder Structure

```
01-docker-terraform/
├── 1_intro/                    # Basic Docker concepts & commands
├── 2_docker_sql/               # Docker + PostgreSQL + data ingestion
│   ├── docker/
│   │   ├── Dockerfile          # Custom ingestion image
│   │   └── docker-compose.yml  # Postgres + pgAdmin setup
│   └── scripts/
│       ├── ingest_data.py      # NYC taxi data ingestion script
│       └── upload_data.py      # Helper for GCS upload
├── 3_terraform_gcp/            # Terraform for GCP
│   └── terraform/
│       ├── main.tf             # GCS bucket + BigQuery dataset
│       ├── variables.tf        # Input variables
│       └── terraform.tfvars    # Your project-specific values (gitignored)
└── homework/
    ├── homework_answers.md     # My answers to the homework questions
    └── queries.sql             # SQL queries used for homework
```

---

## How to Run

### 1. Start PostgreSQL + pgAdmin

```bash
cd 2_docker_sql/docker
docker-compose up -d
```

Then open pgAdmin at http://localhost:8080
- Email: `admin@admin.com`
- Password: `root`

Connect to the server:
- Host: `pgdatabase` (the docker network name)
- Port: `5432`
- Database: `ny_taxi`
- Username: `root`
- Password: `root`

### 2. Ingest NYC Taxi Data

```bash
# Install dependencies
pip install pandas sqlalchemy psycopg2-binary requests

# Run ingestion
python scripts/ingest_data.py \
  --user=root \
  --password=root \
  --host=localhost \
  --port=5432 \
  --db=ny_taxi \
  --table_name=yellow_taxi_trips \
  --url=https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz
```

### 3. Provision GCP Infrastructure with Terraform

```bash
cd 3_terraform_gcp/terraform

# Authenticate with GCP
gcloud auth application-default login

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply changes (creates GCS bucket + BigQuery dataset)
terraform apply

# When done — destroy everything to avoid costs
terraform destroy
```

---

## Key SQL Queries Explored

```sql
-- Count total trips
SELECT COUNT(*) FROM yellow_taxi_trips;

-- Average trip distance
SELECT AVG(trip_distance) FROM yellow_taxi_trips;

-- Top 5 pickup zones by trip count
SELECT 
    zpu."Zone" AS pickup_zone,
    COUNT(*) AS trip_count
FROM yellow_taxi_trips t
JOIN zones zpu ON t."PULocationID" = zpu."LocationID"
GROUP BY pickup_zone
ORDER BY trip_count DESC
LIMIT 5;

-- Revenue by payment type
SELECT 
    payment_type,
    SUM(total_amount) AS total_revenue,
    COUNT(*) AS trip_count
FROM yellow_taxi_trips
GROUP BY payment_type
ORDER BY total_revenue DESC;
```

---

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Terraform GCP Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [NYC TLC Trip Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
- [DataTalksClub Module 1 Notes](https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/01-docker-terraform)
