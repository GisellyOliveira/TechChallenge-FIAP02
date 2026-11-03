-- Jobs do BigQuery da execução bem-sucedida mais completa de cada comando (batch, detect, consume),
-- com os 30 de maior volume faturado de cada uma. As demais execuções ficam resumidas na seção anterior.
WITH ultimas AS (
  SELECT
    run_id,
    ANY_VALUE(command) AS command,
    ARRAY_AGG(status ORDER BY recorded_at DESC LIMIT 1)[OFFSET(0)] AS status,
    MIN(started_at) AS inicio
  FROM `{{ ops }}.runs`
  GROUP BY run_id
),
jobs AS (
  SELECT run_id, COUNT(*) AS n
  FROM `{{ ops }}.steps`
  WHERE job_id IS NOT NULL AND step NOT LIKE 'quality.%' AND step NOT LIKE 'ops.%'
  GROUP BY run_id
),
escolhidas AS (
  SELECT u.run_id, u.command, u.inicio
  FROM ultimas AS u
  JOIN jobs AS j USING (run_id)
  WHERE u.status = 'succeeded'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY u.command ORDER BY j.n DESC, u.inicio DESC) = 1
)
SELECT
  s.run_id, e.command AS comando, s.step AS etapa, s.job_id, s.rows_affected AS linhas,
  s.bytes_processed, s.bytes_billed AS bytes_faturados, s.duration_seconds AS segundos
FROM `{{ ops }}.steps` AS s
JOIN escolhidas AS e USING (run_id)
WHERE s.job_id IS NOT NULL AND s.step NOT LIKE 'quality.%' AND s.step NOT LIKE 'ops.%'
QUALIFY ROW_NUMBER() OVER (PARTITION BY s.run_id ORDER BY s.bytes_billed DESC, s.recorded_at) <= 30
ORDER BY e.inicio, s.bytes_billed DESC;
