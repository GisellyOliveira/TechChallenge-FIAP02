data "google_project" "this" {
  project_id = var.project_id
}

resource "google_pubsub_topic" "eventos" {
  name   = "alfabetizacao-eventos"
  labels = local.labels

  depends_on = [google_project_service.apis]
}

resource "google_pubsub_topic" "dlq" {
  name   = "alfabetizacao-eventos-dlq"
  labels = local.labels

  depends_on = [google_project_service.apis]
}

# Mensagens que falham a entrega 5 vezes vão para a DLQ, em vez de ficarem em loop.
resource "google_pubsub_subscription" "consumer" {
  name                       = "alfabetizacao-eventos-consumer"
  topic                      = google_pubsub_topic.eventos.id
  ack_deadline_seconds       = 60
  message_retention_duration = var.message_retention
  labels                     = local.labels

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dlq.id
    max_delivery_attempts = 5
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "300s"
  }
}

resource "google_pubsub_subscription" "dlq_inspecao" {
  name                 = "alfabetizacao-eventos-dlq-inspecao"
  topic                = google_pubsub_topic.dlq.id
  ack_deadline_seconds = 60
  labels               = local.labels
}

# O agente de serviço do Pub/Sub precisa publicar na DLQ e confirmar mensagens da assinatura.
resource "google_pubsub_topic_iam_member" "dlq_publisher" {
  topic  = google_pubsub_topic.dlq.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_pubsub_subscription_iam_member" "dlq_subscriber" {
  subscription = google_pubsub_subscription.consumer.id
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}
