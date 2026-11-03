-- Commit de um micro-lote de streaming em UMA transação: deduplicação (livro-razão) + MERGE no Gold.
-- Se qualquer passo falhar, nada é gravado e a mensagem será reentregue (ack só depois do commit).
BEGIN TRANSACTION;

INSERT INTO `{{ silver }}.stream_events` (
  event_id, batch_id, source_table, nivel, id_territorio, sigla_uf, ano, rede_codigo,
  taxa_alfabetizacao, meta_ano, meta_final, percentual_participacao,
  origem_dado, source_version, produced_at, first_received_at
)
SELECT
  s.event_id, @batch_id, s.source_table, s.nivel, s.id_territorio, s.sigla_uf, s.ano, s.rede_codigo,
  s.taxa_alfabetizacao, s.meta_ano, s.meta_final, s.percentual_participacao,
  s.origem_dado, s.source_version, s.produced_at, CURRENT_TIMESTAMP()
FROM `{{ staging }}` AS s
WHERE NOT EXISTS (
  SELECT 1 FROM `{{ silver }}.stream_events` AS e WHERE e.event_id = s.event_id
);

{% include "gold/termometro_merge.sql" %}

COMMIT TRANSACTION;
