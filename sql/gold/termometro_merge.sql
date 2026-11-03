{% from "macros.sql" import status_expr %}
-- Termômetro: resultado frente à meta, no MESMO ano e rede. Batch e streaming usam este MERGE,
-- então a regra de status é única. Só atualiza se a versão for mais nova e o valor mudou.
MERGE `{{ gold }}.termometro` AS t
USING (
  WITH fonte AS (
{% include source_template %}
  ),
  unica AS (
    SELECT * FROM fonte
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY nivel, id_territorio, ano, rede_codigo ORDER BY produced_at DESC, event_id DESC
    ) = 1
  )
  SELECT
    u.*,
    COALESCE(d.descricao, 'desconhecido') AS rede_nome,
    {{ status_expr('u.taxa_alfabetizacao', 'u.meta_ano', 'u.ano', meta_window[0]) }} AS status_meta_ano,
    {{ status_expr('u.taxa_alfabetizacao', 'u.meta_final', 'u.ano', meta_window[0]) }} AS status_meta_final,
    u.taxa_alfabetizacao - u.meta_ano AS distancia_meta_ano_pp
  FROM unica AS u
  LEFT JOIN `{{ silver }}.dicionario` AS d
    ON d.id_tabela = 'municipio' AND d.nome_coluna = 'rede' AND d.chave = u.rede_codigo
) AS s
ON t.nivel = s.nivel AND t.id_territorio = s.id_territorio AND t.ano = s.ano AND t.rede_codigo = s.rede_codigo
WHEN MATCHED AND s.produced_at >= t.produced_at AND (
     t.taxa_alfabetizacao IS DISTINCT FROM s.taxa_alfabetizacao
  OR t.meta_ano IS DISTINCT FROM s.meta_ano
  OR t.meta_final IS DISTINCT FROM s.meta_final
  OR t.percentual_participacao IS DISTINCT FROM s.percentual_participacao
) THEN UPDATE SET
  sigla_uf = s.sigla_uf,
  rede_nome = s.rede_nome,
  taxa_alfabetizacao = s.taxa_alfabetizacao,
  meta_ano = s.meta_ano,
  meta_final = s.meta_final,
  percentual_participacao = s.percentual_participacao,
  distancia_meta_ano_pp = s.distancia_meta_ano_pp,
  status_meta_ano = s.status_meta_ano,
  status_meta_final = s.status_meta_final,
  origem_dado = s.origem_dado,
  canal = s.canal,
  source_version = s.source_version,
  produced_at = s.produced_at,
  ultimo_event_id = s.event_id,
  atualizado_em = CURRENT_TIMESTAMP(),
  run_id = @run_id
WHEN NOT MATCHED THEN INSERT (
  nivel, id_territorio, sigla_uf, ano, rede_codigo, rede_nome,
  taxa_alfabetizacao, meta_ano, meta_final, percentual_participacao, distancia_meta_ano_pp,
  status_meta_ano, status_meta_final, origem_dado, canal, source_version, produced_at,
  ultimo_event_id, atualizado_em, run_id
) VALUES (
  s.nivel, s.id_territorio, s.sigla_uf, s.ano, s.rede_codigo, s.rede_nome,
  s.taxa_alfabetizacao, s.meta_ano, s.meta_final, s.percentual_participacao, s.distancia_meta_ano_pp,
  s.status_meta_ano, s.status_meta_final, s.origem_dado, s.canal, s.source_version, s.produced_at,
  s.event_id, CURRENT_TIMESTAMP(), @run_id
);
