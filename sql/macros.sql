{#- Status da meta. SQL padrão (sem funções específicas do BigQuery) para ser testado também em DuckDB.
    Espelha radar_alfabetizacao.domain.indicador.status_meta. -#}
{% macro status_expr(taxa, meta, ano, primeiro_ano_meta) -%}
CASE
  WHEN {{ ano }} < {{ primeiro_ano_meta }} THEN 'linha_de_base'
  WHEN {{ taxa }} IS NULL THEN 'sem_resultado'
  WHEN {{ meta }} IS NULL THEN 'sem_meta'
  WHEN {{ taxa }} >= {{ meta }} THEN 'atingiu'
  ELSE 'nao_atingiu'
END
{%- endmacro %}
