output "gcs_bucket_name" {
  description = "Name of the created GCS data lake bucket"
  value       = google_storage_bucket.data_lake.name
}

output "gcs_bucket_url" {
  description = "URL of the GCS bucket"
  value       = google_storage_bucket.data_lake.url
}

output "bigquery_dataset_id" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.warehouse.dataset_id
}

output "bigquery_dataset_url" {
  description = "Link to the BigQuery dataset in GCP console"
  value       = "https://console.cloud.google.com/bigquery?project=${var.project}&d=${var.bq_dataset_name}"
}
