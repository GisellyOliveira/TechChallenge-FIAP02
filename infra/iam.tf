resource "google_service_account" "runner" {
  account_id   = "radar-runner"
  display_name = "Radar da Alfabetização: execução dos jobs"
}

resource "google_service_account" "scheduler" {
  account_id   = "radar-scheduler"
  display_name = "Radar da Alfabetização: disparo agendado"
}

# Privilégio mínimo: o job só cria jobs/dados no BigQuery, usa o Pub/Sub e escreve no bucket.
resource "google_project_iam_member" "runner_bq_jobs" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.runner.email}"
}

resource "google_bigquery_dataset_iam_member" "runner_editor" {
  for_each   = google_bigquery_dataset.layers
  dataset_id = each.value.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.runner.email}"
}

resource "google_pubsub_topic_iam_member" "runner_publisher" {
  topic  = google_pubsub_topic.eventos.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.runner.email}"
}

resource "google_pubsub_subscription_iam_member" "runner_subscriber" {
  subscription = google_pubsub_subscription.consumer.id
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${google_service_account.runner.email}"
}

resource "google_storage_bucket_iam_member" "runner_objects" {
  bucket = google_storage_bucket.bronze.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.runner.email}"
}

# O job lê o tamanho do bucket para a projeção FinOps.
resource "google_storage_bucket_iam_member" "runner_bucket_reader" {
  bucket = google_storage_bucket.bronze.name
  role   = "roles/storage.legacyBucketReader"
  member = "serviceAccount:${google_service_account.runner.email}"
}
