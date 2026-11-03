SELECT run_id, layer AS camada, severity AS severidade,
  COUNTIF(passed) AS aprovadas, COUNTIF(NOT passed) AS reprovadas
FROM `{{ ops }}.quality_results`
GROUP BY run_id, camada, severidade
ORDER BY MAX(checked_at) DESC, camada
LIMIT 40;
