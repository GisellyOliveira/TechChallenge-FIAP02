# Evidências de execução na nuvem

Projeto GCP `dados-basedosdados`, região US (Cloud Run e bucket em `us-central1`). Tudo o que está nesta pasta vem
de execuções reais; nada foi simulado, exceto as mensagens defeituosas do streaming, que levam `origem=simulado`.

* [`evidencias.md`](evidencias.md): gerado por `make evidence` direto das tabelas `alfabetizacao_ops` (job IDs, linhas,
  bytes faturados, qualidade por camada, regras reprovadas, lotes de streaming, contagem de linhas por tabela).
* Os prints do console estão abaixo, na ordem do pipeline.

## BigQuery: Medalhão e registro operacional

Os quatro datasets, criados pelo Terraform (etiqueta `goog-terraform-provisioned`), na região US.

![Datasets](01-bigquery-datasets.png)

| Camada | Print |
|---|---|
| Bronze: cópia versionada da fonte, `stream_events` e a view de quarentena | ![Bronze](01a-bigquery-bronze-tabelas.png) |
| Silver: tabelas tipadas e validadas | ![Silver](01b-bigquery-silver-tabelas.png) |
| Gold: termômetro, reconciliação, indicador municipal e tabelas para a Fase 3 | ![Gold](01c-bigquery-gold-tabelas.png) |
| Ops: execuções, passos, regras de qualidade e versões processadas | ![Ops](01d-bigquery-ops-tabelas.png) |
| Ops: lotes do streaming (`stream_batches`) e as tabelas temporárias `stg_*`, que expiram em 24 h | ![Ops, lotes](01e-bigquery-ops-stream-batches.png) |

## Cloud Run: jobs

![Jobs](02-cloud-run-jobs.png)

Execução concluída do `radar-batch` (fonte inalterada: `skipped_no_changes`):

![Execução do radar-batch](02-cloud-run-batch-execucoes.png)

## Pub/Sub: tópicos e assinaturas

Tópico de eventos, tópico de mensagens mortas (DLQ), assinatura do consumidor e assinatura de inspeção da DLQ.

![Tópicos](03-pubsub-topicos.png)

![Assinaturas](03-pubsub-assinaturas.png)

## Cloud Logging: falha do gate de qualidade

Log estruturado `run_failed` da demonstração (`--demo-gate-failure`): o gate bloqueou a Silver e a Gold ficou intacta.

![Logging](04-logging-run-failed.png)

## Monitoring: política e alerta

A política "Radar: execução falhou" é alimentada pela métrica baseada em logs `radar_run_failed`.

![Política de alerta](05-monitoring-politica.png)

E-mail recebido quando a falha demonstrativa disparou o alerta:

![E-mail do alerta](07-alerta-email.png)

## Cloud Storage: Bronze em Parquet

Um arquivo Parquet por versão da fonte (`source_version`), em `bronze/table=<tabela>/source_version=<hash>/`.

![Parquet na Bronze](06-storage-parquet.png)
