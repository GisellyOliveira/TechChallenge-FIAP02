SELECT run_id, rule_id AS regra, severity AS severidade, observed AS observado, expectation AS esperado
FROM `{{ ops }}.quality_results`
WHERE NOT passed
ORDER BY checked_at DESC
LIMIT 30;
