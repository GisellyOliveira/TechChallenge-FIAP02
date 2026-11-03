-- Metas oficiais padronizadas: rede em código, meta do ano do resultado (`meta_ano`), meta do ano
-- seguinte (insumo da Fase 3) e meta final. As colunas por ano vêm do schema REAL da fonte, então
-- uma coluna nova (ex.: meta_alfabetizacao_2031) é absorvida sem mudar o código.
CREATE OR REPLACE TABLE `{{ silver }}.{{ spec.target }}` AS
SELECT
  {{ spec.id_expr }} AS id_territorio,
  {{ spec.uf_expr }} AS sigla_uf,
  b.ano,
  CASE b.rede
{% for texto, codigo in meta_rede_map.items() %}
    WHEN '{{ texto }}' THEN '{{ codigo }}'
{% endfor %}
  END AS rede_codigo,
  b.rede AS rede_texto,
  b.taxa_alfabetizacao,
  CASE b.ano
{% for y in years %}
    WHEN {{ y }} THEN b.meta_alfabetizacao_{{ y }}
{% endfor %}
  END AS meta_ano,
  CASE b.ano
{% for y in years %}
    WHEN {{ y - 1 }} THEN b.meta_alfabetizacao_{{ y }}
{% endfor %}
  END AS meta_ano_seguinte,
  b.meta_alfabetizacao_{{ meta_window[1] }} AS meta_final,
  b.percentual_participacao,
  {{ spec.nivel_alfabetizacao_expr }} AS nivel_alfabetizacao
FROM `{{ bronze }}.{{ spec.source }}` AS b
{% if spec.join_uf %}
LEFT JOIN `{{ silver }}.ref_uf` AS u ON u.codigo_ibge = LEFT(b.id_municipio, 2)
{% endif %}
WHERE b._source_version = '{{ versions[spec.source] }}';
