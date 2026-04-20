variable "project" {
  description = "Your GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "us-central1"
}

variable "bucket_suffix" {
  description = "Suffix to make the GCS bucket name globally unique"
  type        = string
  default     = "bucket"
}

variable "bq_dataset_name" {
  description = "BigQuery dataset name"
  type        = string
  default     = "ny_taxi_warehouse"
}
