-- Fase 3: RÓTULOS do ano-alvo (t+1). `split_sugerido` é temporal: o ano-alvo mais recente vira teste
-- assim que houver mais de um ano-alvo; enquanto houver só um, todos ficam em treino.
CREATE OR REPLACE TABLE `{{ gold }}.ml_labels`
CLUSTER BY ano_alvo AS
WITH janela AS (
  SELECT MAX(ano) AS ultimo_ano, COUNT(DISTINCT ano) AS anos
  FROM `{{ gold }}.termometro`
  WHERE nivel = 'municipio' AND status_meta_ano IN ('atingiu', 'nao_atingiu')
)
SELECT
  t.id_territorio AS id_municipio,
  t.rede_codigo,
  t.ano AS ano_alvo,
  t.ano - 1 AS ano_referencia,
  t.taxa_alfabetizacao AS taxa_alvo,
  t.status_meta_ano = 'atingiu' AS atingiu_meta_alvo,
  IF(j.anos > 1 AND t.ano = j.ultimo_ano, 'teste', 'treino') AS split_sugerido
FROM `{{ gold }}.termometro` AS t
CROSS JOIN janela AS j
WHERE t.nivel = 'municipio' AND t.status_meta_ano IN ('atingiu', 'nao_atingiu');
