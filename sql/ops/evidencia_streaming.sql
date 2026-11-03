SELECT batch_id, pulled AS recebidas, valid AS validas, quarantined AS quarentena,
  duplicates_in_batch AS dup_no_lote, duplicates_ledger AS dup_no_ledger, merged_new AS integradas,
  ROUND(latency_p50_seconds, 2) AS latencia_p50_s, ROUND(latency_p95_seconds, 2) AS latencia_p95_s
FROM `{{ ops }}.stream_batches`
ORDER BY recorded_at DESC
LIMIT 20;
