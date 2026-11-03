-- Esquema operacional e tabelas de destino. Idempotente: pode rodar a cada execução.
-- Os datasets são criados pelo Terraform (infra/main.tf).

CREATE TABLE IF NOT EXISTS `{{ ops }}.runs` (
  run_id STRING NOT NULL,
  command STRING,
  status STRING,
  started_at TIMESTAMP,
  finished_at TIMESTAMP,
  error STRING,
  params STRING,
  recorded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `{{ ops }}.steps` (
  run_id STRING,
  step STRING,
  status STRING,
  job_id STRING,
  rows_affected INT64,
  bytes_processed INT64,
  bytes_billed INT64,
  duration_seconds FLOAT64,
  detail STRING,
  recorded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `{{ ops }}.quality_results` (
  run_id STRING,
  layer STRING,
  rule_id STRING,
  severity STRING,
  passed BOOL,
  observed FLOAT64,
  expectation STRING,
  message STRING,
  checked_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `{{ ops }}.source_versions` (
  table_name STRING,
  consumer STRING,
  source_version STRING,
  source_modified_at TIMESTAMP,
  num_rows INT64,
  num_bytes INT64,
  run_id STRING,
  recorded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `{{ ops }}.stream_batches` (
  batch_id STRING,
  run_id STRING,
  pulled INT64,
  valid INT64,
  quarantined INT64,
  duplicates_in_batch INT64,
  duplicates_ledger INT64,
  merged_new INT64,
  latency_p50_seconds FLOAT64,
  latency_p95_seconds FLOAT64,
  duration_seconds FLOAT64,
  status STRING,
  recorded_at TIMESTAMP
);

-- Bronze do streaming: TODA mensagem recebida, válida ou não (append-only).
CREATE TABLE IF NOT EXISTS `{{ bronze }}.stream_events` (
  message_id STRING,
  event_id STRING,
  payload STRING,
  publish_time TIMESTAMP,
  received_at TIMESTAMP,
  batch_id STRING,
  valid BOOL,
  reasons STRING
);

CREATE OR REPLACE VIEW `{{ bronze }}.stream_quarantine` AS
SELECT * FROM `{{ bronze }}.stream_events` WHERE NOT valid;

-- Silver do streaming: eventos válidos e únicos (livro-razão de deduplicação).
CREATE TABLE IF NOT EXISTS `{{ silver }}.stream_events` (
  event_id STRING NOT NULL,
  batch_id STRING,
  source_table STRING,
  nivel STRING,
  id_territorio STRING,
  sigla_uf STRING,
  ano INT64,
  rede_codigo STRING,
  taxa_alfabetizacao FLOAT64,
  meta_ano FLOAT64,
  meta_final FLOAT64,
  percentual_participacao FLOAT64,
  origem_dado STRING,
  source_version STRING,
  produced_at TIMESTAMP,
  first_received_at TIMESTAMP
);

-- Gold: Termômetro, alimentado pelo batch e pelo streaming com a mesma regra (MERGE).
CREATE TABLE IF NOT EXISTS `{{ gold }}.termometro` (
  nivel STRING NOT NULL,
  id_territorio STRING NOT NULL,
  sigla_uf STRING,
  ano INT64 NOT NULL,
  rede_codigo STRING NOT NULL,
  rede_nome STRING,
  taxa_alfabetizacao FLOAT64,
  meta_ano FLOAT64,
  meta_final FLOAT64,
  percentual_participacao FLOAT64,
  distancia_meta_ano_pp FLOAT64,
  status_meta_ano STRING,
  status_meta_final STRING,
  origem_dado STRING,
  canal STRING,
  source_version STRING,
  produced_at TIMESTAMP,
  ultimo_event_id STRING,
  atualizado_em TIMESTAMP,
  run_id STRING
)
CLUSTER BY nivel, ano;
