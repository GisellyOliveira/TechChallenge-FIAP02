{% for s in batch_sources %}
SELECT
  '{{ s.nivel }}' AS nivel, id_territorio, sigla_uf, ano, rede_codigo,
  taxa_alfabetizacao, meta_ano, meta_final, percentual_participacao,
  'oficial' AS origem_dado, '{{ s.version }}' AS source_version,
  TIMESTAMP '{{ s.modified }}' AS produced_at, CAST(NULL AS STRING) AS event_id,
  'batch' AS canal
FROM `{{ silver }}.{{ s.table }}`
{{ "UNION ALL" if not loop.last else "" }}
{% endfor %}
