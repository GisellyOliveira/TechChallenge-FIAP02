-- Arquivo imutável da versão no Cloud Storage (Parquet + Snappy), particionado por versão.
EXPORT DATA OPTIONS (
  uri = 'gs://{{ bucket }}/bronze/table={{ table }}/source_version={{ version }}/part-*.parquet',
  format = 'PARQUET',
  compression = 'SNAPPY',
  overwrite = true
) AS
SELECT * EXCEPT (_run_id, _source_version, _ingested_at)
FROM `{{ bronze }}.{{ table }}`
WHERE _source_version = '{{ version }}';
