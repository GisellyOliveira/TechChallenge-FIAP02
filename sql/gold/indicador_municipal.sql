-- Gold municipal (rede municipal): Termômetro + reconciliação + detecção de anomalias.
-- O selo de confiança resume quanto o indicador publicado pode ser tomado como está:
--   baixa: microdados divergem do oficial acima do limiar, ou amostra pequena;
--   media: queda brusca frente ao ano anterior, ou sem microdados para conferir;
--   alta : nenhuma sinalização.
CREATE OR REPLACE TABLE `{{ gold }}.indicador_municipal`
CLUSTER BY sigla_uf, ano AS
WITH base AS (
  SELECT
    t.id_territorio AS id_municipio, t.sigla_uf, t.ano, t.rede_codigo, t.rede_nome,
    t.taxa_alfabetizacao, t.meta_ano, t.meta_final, t.distancia_meta_ano_pp,
    t.status_meta_ano, t.status_meta_final, t.percentual_participacao,
    r.taxa_oficial AS taxa_oficial_municipio, r.taxa_recalculada, r.diferenca_pp, r.alunos_avaliados,
    LAG(t.taxa_alfabetizacao) OVER (
      PARTITION BY t.id_territorio, t.rede_codigo ORDER BY t.ano
    ) AS taxa_ano_anterior,
    t.origem_dado, t.canal, t.source_version, t.atualizado_em
  FROM `{{ gold }}.termometro` AS t
  LEFT JOIN `{{ gold }}.reconciliacao` AS r
    ON r.nivel = 'municipio' AND r.id_territorio = t.id_territorio
   AND r.ano = t.ano AND r.rede_codigo = t.rede_codigo
  WHERE t.nivel = 'municipio'
),
sinais AS (
  SELECT
    base.*,
    taxa_alfabetizacao - taxa_ano_anterior AS variacao_pp,
    taxa_recalculada IS NULL AS flag_sem_microdados,
    COALESCE(alunos_avaliados < {{ anomaly.min_alunos_avaliados }}, FALSE) AS flag_amostra_pequena,
    COALESCE(ABS(diferenca_pp) > {{ anomaly.max_divergencia_pp }}, FALSE) AS flag_divergencia_oficial,
    COALESCE(taxa_alfabetizacao - taxa_ano_anterior <= -{{ anomaly.queda_brusca_pp }}, FALSE) AS flag_queda_brusca
  FROM base
)
SELECT
  sinais.*,
  CASE
    WHEN flag_divergencia_oficial OR flag_amostra_pequena THEN 'baixa'
    WHEN flag_queda_brusca OR flag_sem_microdados THEN 'media'
    ELSE 'alta'
  END AS selo_confianca
FROM sinais;
