terraform {
  required_version = ">= 1.7"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region
}

# -------------------------------------------------------
# Google Cloud Storage — Data Lake Bucket
# -------------------------------------------------------
resource "google_storage_bucket" "data_lake" {
  name          = "${var.project}-data-lake-${var.bucket_suffix}"
  location      = var.region
  force_destroy = true   # Allows terraform destroy to delete non-empty buckets

  # Automatically delete old versions of objects (cost saving)
  lifecycle_rule {
    condition {
      age = 30  # days
    }
    action {
      type = "Delete"
    }
  }

  # Best practice: prevent accidental public access
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# -------------------------------------------------------
# BigQuery — Data Warehouse Dataset
# -------------------------------------------------------
resource "google_bigquery_dataset" "warehouse" {
  dataset_id  = var.bq_dataset_name
  project     = var.project
  location    = var.region
  description = "DE Zoomcamp data warehouse dataset"

  # Allow terraform destroy to delete even if tables exist
  delete_contents_on_destroy = true
}
