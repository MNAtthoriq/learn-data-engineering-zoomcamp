output "project_id" {
  value = var.project_id
}

output "region" {
  value = var.region
}

output "bucket_name" {
  value = google_storage_bucket.data_lake.name
}

output "dataset_id" {
  value = google_bigquery_dataset.warehouse.dataset_id
}

output "kestra_service_account_email" {
  value = google_service_account.kestra.email
}

output "kestra_service_account_key_base64" {
  value = google_service_account_key.kestra_key.private_key
  sensitive = true
}