-- Última versão da fonte já processada por consumidor ('batch' ou 'stream').
SELECT table_name, source_version
FROM `{{ ops }}.source_versions`
WHERE consumer = @consumer
QUALIFY ROW_NUMBER() OVER (PARTITION BY table_name ORDER BY recorded_at DESC) = 1;
