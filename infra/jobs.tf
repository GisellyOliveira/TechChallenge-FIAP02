locals {
  jobs = {
    batch   = { args = ["batch"], timeout = "900s", schedule = "0 6 * * *" }
    detect  = { args = ["detect"], timeout = "300s", schedule = "0 */6 * * *" }
    consume = { args = ["consume"], timeout = "900s", schedule = "*/30 * * * *" }
  }
}

resource "google_cloud_run_v2_job" "radar" {
  for_each            = var.create_jobs ? local.jobs : {}
  name                = "radar-${each.key}"
  location            = var.region
  deletion_protection = false
  labels              = local.labels

  template {
    template {
      service_account = google_service_account.runner.email
      timeout         = each.value.timeout
      max_retries     = 1

      containers {
        image = local.image
        args  = each.value.args

        env {
          name  = "RADAR_PROJECT_ID"
          value = var.project_id
        }
        env {
          name  = "RADAR_BUCKET"
          value = google_storage_bucket.bronze.name
        }

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_v2_job_iam_member" "scheduler_invoker" {
  for_each = google_cloud_run_v2_job.radar
  name     = each.value.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_cloud_scheduler_job" "radar" {
  for_each    = var.create_jobs ? local.jobs : {}
  name        = "radar-${each.key}"
  region      = var.region
  schedule    = each.value.schedule
  time_zone   = "America/Sao_Paulo"
  paused      = !var.scheduler_enabled
  description = "Dispara o job radar-${each.key}"

  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/radar-${each.key}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

  depends_on = [google_cloud_run_v2_job.radar]
}
