-- Bronze append-only: uma nova versão da tabela de origem só entra se ainda não existir.
-- 1) cria a tabela (vazia) com o schema da fonte mais as colunas de linhagem;
-- 2) acrescenta colunas que a fonte ganhou depois, em UMA instrução (limite de atualizações de
--    metadados por tabela); versões antigas ficam com NULL nessas colunas;
-- 3) insere a versão por NOME de coluna, então a ordem das colunas nunca importa.
CREATE TABLE IF NOT EXISTS `{{ bronze }}.{{ table }}` AS
SELECT
  s.*,
  CAST(NULL AS STRING) AS _run_id,
  CAST(NULL AS STRING) AS _source_version,
  CAST(NULL AS TIMESTAMP) AS _ingested_at
FROM `{{ src }}.{{ table }}` AS s
WHERE FALSE;

ALTER TABLE `{{ bronze }}.{{ table }}`
{% for name, type in columns.items() %}
  ADD COLUMN IF NOT EXISTS `{{ name }}` {{ type }}{{ "," if not loop.last else ";" }}
{% endfor %}

-- A guarda IF evita até a leitura da fonte quando a versão já está na Bronze (reexecução com --force).
IF NOT EXISTS (
  SELECT 1 FROM `{{ bronze }}.{{ table }}` AS b WHERE b._source_version = @source_version
) THEN
  INSERT INTO `{{ bronze }}.{{ table }}` (
{% for name in columns %}
    `{{ name }}`,
{% endfor %}
    _run_id, _source_version, _ingested_at
  )
  SELECT
{% for name in columns %}
    s.`{{ name }}`,
{% endfor %}
    @run_id AS _run_id,
    @source_version AS _source_version,
    CURRENT_TIMESTAMP() AS _ingested_at
  FROM `{{ src }}.{{ table }}` AS s;
END IF;
