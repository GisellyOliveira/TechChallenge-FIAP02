# Cada falha de execução emite um log estruturado com event="run_failed" (ver logging_setup.py).
resource "google_logging_metric" "run_failed" {
  name        = "radar_run_failed"
  description = "Execuções do Radar que terminaram em falha"
  filter      = "jsonPayload.event=\"run_failed\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
  }

  depends_on = [google_project_service.apis]
}

resource "google_monitoring_notification_channel" "email" {
  display_name = "Radar: alerta por e-mail"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }

  depends_on = [google_project_service.apis]
}

resource "google_monitoring_alert_policy" "run_failed" {
  display_name = "Radar: execução falhou"
  combiner     = "OR"

  conditions {
    display_name = "Pelo menos uma execução com falha em 5 minutos"

    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.run_failed.name}\" AND resource.type=\"cloud_run_job\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]

  alert_strategy {
    auto_close = "86400s"
  }
}
