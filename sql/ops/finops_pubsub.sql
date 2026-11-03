-- Volume de mensagens de streaming efetivamente recebidas (base do custo de Pub/Sub).
SELECT COUNT(*) AS mensagens, COALESCE(SUM(LENGTH(payload)), 0) AS bytes
FROM `{{ bronze }}.stream_events`;
