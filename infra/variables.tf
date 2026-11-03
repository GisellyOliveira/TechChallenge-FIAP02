variable "project_id" {
  description = "ID do projeto GCP onde tudo é criado."
  type        = string
}

variable "region" {
  description = "Região dos serviços regionais (Cloud Run, Artifact Registry, Cloud Storage)."
  type        = string
  default     = "us-central1"
}

variable "bq_location" {
  description = "Localização dos datasets do BigQuery. Precisa ser a mesma da fonte pública (US)."
  type        = string
  default     = "US"
}

variable "bucket_name" {
  description = "Nome globalmente único do bucket da Bronze em Parquet."
  type        = string
}

variable "alert_email" {
  description = "E-mail que recebe o alerta de falha de execução."
  type        = string
}

variable "image_tag" {
  description = "Tag da imagem em Artifact Registry usada pelos Cloud Run Jobs."
  type        = string
  default     = "latest"
}

variable "create_jobs" {
  description = "Cria os Cloud Run Jobs. Só ligue depois que a imagem existir no Artifact Registry."
  type        = bool
  default     = false
}

variable "scheduler_enabled" {
  description = "Liga os agendamentos recorrentes. Desligado por padrão para não gerar custo sem querer."
  type        = bool
  default     = false
}

variable "message_retention" {
  description = "Retenção de mensagens não consumidas na assinatura."
  type        = string
  default     = "604800s"
}
