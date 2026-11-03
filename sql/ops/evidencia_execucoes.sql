SELECT
  run_id,
  ANY_VALUE(command) AS comando,
  ARRAY_AGG(status ORDER BY recorded_at DESC LIMIT 1)[OFFSET(0)] AS status,
  MIN(started_at) AS inicio,
  TIMESTAMP_DIFF(MAX(finished_at), MIN(started_at), SECOND) AS segundos,
  ARRAY_AGG(error IGNORE NULLS ORDER BY recorded_at DESC LIMIT 1)[SAFE_OFFSET(0)] AS erro
FROM `{{ ops }}.runs`
GROUP BY run_id
ORDER BY inicio DESC
LIMIT 30;
