-- Referência territorial: prefixo IBGE (2 dígitos) -> sigla da UF. Vem de config/sources.yaml.
CREATE OR REPLACE TABLE `{{ silver }}.ref_uf` AS
SELECT codigo_ibge, sigla_uf
FROM UNNEST([
{% for codigo, sigla in uf_ibge.items() %}
  STRUCT('{{ codigo }}' AS codigo_ibge, '{{ sigla }}' AS sigla_uf){{ "," if not loop.last else "" }}
{% endfor %}
]);
