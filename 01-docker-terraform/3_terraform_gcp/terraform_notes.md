# Terraform & GCP — Notes

## What is Infrastructure as Code (IaC)?

IaC means defining your cloud infrastructure in code files, the same way you write application code. Instead of manually clicking through GCP console to create resources, you write `.tf` files and Terraform handles creation, updates, and deletion automatically.

### Benefits

| Without IaC | With IaC (Terraform) |
|-------------|---------------------|
| Click through GCP console | Write `.tf` config files |
| Hard to reproduce | `terraform apply` = identical infra every time |
| No audit trail | Git history shows every change |
| Manual teardown (risk of forgetting) | `terraform destroy` removes everything |
| Prone to human error | Validated before applying |

---

## Terraform Core Concepts

### Providers

Providers are plugins that let Terraform talk to a cloud platform:

```hcl
provider "google" {
  project = "my-project-id"
  region  = "us-central1"
}
```

Terraform supports AWS, Azure, GCP, Kubernetes, and hundreds more.

### Resources

Resources are the actual infrastructure components you create:

```hcl
resource "google_storage_bucket" "my_bucket" {
  name     = "my-unique-bucket-name"
  location = "US"
}
```

Format: `resource "<provider_resource_type>" "<local_name>" { ... }`

### Variables

Variables make configs reusable across environments:

```hcl
# variables.tf — declares the variable
variable "project" {
  description = "GCP Project ID"
  type        = string
}

# terraform.tfvars — provides the value
project = "my-actual-project-id"

# main.tf — uses the variable
provider "google" {
  project = var.project
}
```

### Outputs

Outputs display useful info after `terraform apply`:

```hcl
output "bucket_name" {
  value = google_storage_bucket.my_bucket.name
}
```

---

## Terraform Workflow

```bash
terraform init      # Download providers, initialize working directory
terraform fmt       # Format .tf files (good practice)
terraform validate  # Check syntax without connecting to GCP
terraform plan      # Preview what WILL be created/changed/destroyed
terraform apply     # Actually create the resources (asks for confirmation)
terraform destroy   # Delete ALL resources defined in the config
```

**Always run `plan` before `apply`** — it shows exactly what will change.

---

## GCP Resources We Create

### Google Cloud Storage (GCS) Bucket — Data Lake

A GCS bucket is an object store (like S3 on AWS). We use it as our **data lake** — a place to dump raw data before processing.

```hcl
resource "google_storage_bucket" "data_lake" {
  name     = "my-project-data-lake"
  location = "us-central1"
  
  # Auto-delete old files after 30 days (saves money)
  lifecycle_rule {
    condition { age = 30 }
    action    { type = "Delete" }
  }
}
```

### BigQuery Dataset — Data Warehouse

BigQuery is GCP's serverless data warehouse. A **dataset** is a container for tables:

```hcl
resource "google_bigquery_dataset" "warehouse" {
  dataset_id = "ny_taxi_warehouse"
  location   = "US"
}
```

---

## GCP Authentication

Before Terraform can create resources in GCP, you need to authenticate:

```bash
# Option 1: Application Default Credentials (recommended for local dev)
gcloud auth application-default login

# Option 2: Service Account Key (recommended for CI/CD)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

For a service account, grant it these roles:
- `Storage Admin` — manage GCS buckets
- `BigQuery Admin` — create BigQuery datasets
- `Viewer` — read project metadata

---

## Data Lake vs Data Warehouse

| | Data Lake (GCS) | Data Warehouse (BigQuery) |
|--|----------------|--------------------------|
| **Format** | Raw files (CSV, Parquet, JSON) | Structured tables |
| **Schema** | Schema-on-read | Schema-on-write |
| **Purpose** | Store everything cheaply | Analytical queries |
| **Access** | Files / APIs | SQL |
| **Cost** | Very cheap storage | Pay-per-query |

In our pipeline: raw data lands in GCS → gets transformed → loaded into BigQuery for analysis.
