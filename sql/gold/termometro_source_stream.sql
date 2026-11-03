SELECT
  nivel, id_territorio, sigla_uf, ano, rede_codigo,
  taxa_alfabetizacao, meta_ano, meta_final, percentual_participacao,
  origem_dado, source_version, produced_at, event_id,
  'stream' AS canal
FROM `{{ silver }}.stream_events`
WHERE batch_id = @batch_id
