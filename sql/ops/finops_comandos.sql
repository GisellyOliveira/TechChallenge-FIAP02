-- Custo médio MEDIDO por tipo de execução bem-sucedida (bytes faturados e duração).
-- "completo" = a execução teve trabalho (fonte mudou / havia mensagens); "sem_mudancas" = execução ociosa.
-- Separar as duas variantes é o que permite projetar o mês: no dia a dia quase tudo é ocioso.
WITH ultimas AS (
  SELECT
    run_id,
    ANY_VALUE(command) AS command,
    ARRAY_AGG(status ORDER BY recorded_at DESC LIMIT 1)[OFFSET(0)] AS status,
    MIN(started_at) AS started_at,
    MAX(finished_at) AS finished_at
  FROM `{{ ops }}.runs`
  GROUP BY run_id
),
passos AS (
  SELECT
    run_id,
    SUM(bytes_billed) AS bytes_billed,
    LOGICAL_OR(step = 'batch.sem_mudancas') AS batch_ocioso,
    LOGICAL_OR(step LIKE 'detect.read.%') AS detect_trabalhou,
    LOGICAL_OR(step = 'stream.commit') AS consume_trabalhou
  FROM `{{ ops }}.steps`
  GROUP BY run_id
)
SELECT
  u.command AS comando,
  IF(
    CASE u.command
      WHEN 'batch' THEN NOT p.batch_ocioso
      WHEN 'detect' THEN p.detect_trabalhou
      WHEN 'consume' THEN p.consume_trabalhou
      ELSE TRUE
    END,
    'completo', 'sem_mudancas'
  ) AS variante,
  COUNT(*) AS execucoes,
  AVG(p.bytes_billed) AS bytes_faturados_medios,
  AVG(TIMESTAMP_DIFF(u.finished_at, u.started_at, MILLISECOND) / 1000) AS segundos_medios
FROM ultimas AS u
JOIN passos AS p USING (run_id)
WHERE u.status = 'succeeded'
GROUP BY comando, variante;
