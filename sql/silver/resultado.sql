-- Resultados oficiais agregados (municipio e uf): mantém todas as colunas da fonte e acrescenta a
-- descrição da rede (dicionário) e, para municípios, a sigla da UF derivada do código IBGE.
CREATE OR REPLACE TABLE `{{ silver }}.{{ table }}` AS
SELECT
  b.* EXCEPT (_run_id, _source_version, _ingested_at),
{% if derive_uf %}
  u.sigla_uf,
{% endif %}
  COALESCE(d.descricao, 'desconhecido') AS rede_nome
FROM `{{ bronze }}.{{ table }}` AS b
{% if derive_uf %}
LEFT JOIN `{{ silver }}.ref_uf` AS u ON u.codigo_ibge = LEFT(b.id_municipio, 2)
{% endif %}
LEFT JOIN `{{ silver }}.dicionario` AS d
  ON d.id_tabela = '{{ table }}' AND d.nome_coluna = 'rede' AND d.chave = b.rede
WHERE b._source_version = '{{ versions[table] }}';
