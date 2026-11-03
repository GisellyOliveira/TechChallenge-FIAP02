-- Eventos do micro-lote que já estão no livro-razão (reentrega ou republicação).
SELECT COUNT(*) AS observed
FROM `{{ staging }}`
WHERE event_id IN (SELECT event_id FROM `{{ silver }}.stream_events`);
