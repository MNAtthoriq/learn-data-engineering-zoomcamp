terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "required" {
  for_each = toset([
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
  ])
  project            = var.project_id
  service            = each.value
  # keep APIs for other projects
  disable_on_destroy = false 
}

resource "google_storage_bucket" "data_lake" {
  project = var.project_id
  location = var.region
  name = var.bucket_name
  uniform_bucket_level_access = true
  # since it is for learning purpose, it will remove bucket when `terraform destroy`
  force_destroy = true

  lifecycle_rule {
    condition {
      age = var.raw_data_retention_days
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [ google_project_service.required ]
}

resource "google_bigquery_dataset" "warehouse" {
  project = var.project_id
  location = var.region
  dataset_id = var.dataset_id
  
  depends_on = [ google_project_service.required ]
}

# runtime identity for kestra, since it is using locally, it needed using key and can't using workload identity
resource "google_service_account" "kestra" {
  project = var.project_id
  account_id = var.service_account_id
  display_name = "Kestra taxi pipeline runtime service account"

  depends_on = [ google_project_service.required ]
}

resource "google_service_account_key" "kestra_key" {
  service_account_id = google_service_account.kestra.name
}

resource "google_storage_bucket_iam_member" "kestra_bucket_access" {
  bucket = google_storage_bucket.data_lake.name
  role = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.kestra.email}"
}

resource "google_bigquery_dataset_iam_member" "kestra_dataset_access" {
  project = var.project_id
  dataset_id = google_bigquery_dataset.warehouse.dataset_id
  role = "roles/bigquery.dataEditor"
  member = "serviceAccount:${google_service_account.kestra.email}"
}

resource "google_project_iam_member" "kestra_job_user" {
  project = var.project_id
  role = "roles/bigquery.jobUser"
  member = "serviceAccount:${google_service_account.kestra.email}"
}