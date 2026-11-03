-- Eventos já integrados de uma tabela de origem (para não republicar o que não mudou).
SELECT event_id FROM `{{ silver }}.stream_events` WHERE source_table = @table;
