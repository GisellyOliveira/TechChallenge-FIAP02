locals {
  image = "${var.region}-docker.pkg.dev/${var.project_id}/radar/radar-alfabetizacao:${var.image_tag}"

  datasets = {
    bronze = "Dados brutos versionados, exatamente como a fonte oficial entregou."
    silver = "Dados tipados, validados e com chaves normalizadas."
    gold   = "Indicadores prontos para uso: termômetro, reconciliação, anomalias e base de ML."
    ops    = "Registro operacional: execuções, etapas, qualidade, versões da fonte e lotes de streaming."
  }

  required_apis = [
    "bigquery.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "cloudscheduler.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "storage.googleapis.com",
  ]

  labels = {
    app = "radar-alfabetizacao"
  }
}

resource "google_project_service" "apis" {
  for_each           = toset(local.required_apis)
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "radar" {
  repository_id = "radar"
  location      = var.region
  format        = "DOCKER"
  description   = "Imagens do Radar da Alfabetização"
  labels        = local.labels

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket" "bronze" {
  name                        = var.bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true
  labels                      = local.labels

  depends_on = [google_project_service.apis]
}

resource "google_bigquery_dataset" "layers" {
  for_each                   = local.datasets
  dataset_id                 = "alfabetizacao_${each.key}"
  location                   = var.bq_location
  description                = each.value
  labels                     = local.labels
  delete_contents_on_destroy = true

  depends_on = [google_project_service.apis]
}
