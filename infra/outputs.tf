output "image" {
  description = "Imagem esperada pelos Cloud Run Jobs."
  value       = local.image
}

output "bucket" {
  value = google_storage_bucket.bronze.name
}

output "runner_service_account" {
  value = google_service_account.runner.email
}

output "topic" {
  value = google_pubsub_topic.eventos.name
}

output "subscription" {
  value = google_pubsub_subscription.consumer.name
}
