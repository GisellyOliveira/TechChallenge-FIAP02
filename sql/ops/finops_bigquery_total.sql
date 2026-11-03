-- Total de bytes faturados pelo pipeline (jobs com o rótulo app=radar-alfabetizacao).
SELECT COUNT(*) AS jobs, COALESCE(SUM(total_bytes_billed), 0) AS bytes_faturados
FROM `{{ region }}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @dias DAY)
  AND job_type = 'QUERY'
  AND state = 'DONE'
  AND error_result IS NULL
  AND EXISTS (SELECT 1 FROM UNNEST(labels) AS l WHERE l.key = 'app' AND l.value = 'radar-alfabetizacao');
