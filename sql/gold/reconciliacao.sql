-- Validação cruzada: taxa recalculada dos microdados (ponderada por peso_aluno, entre avaliados,
-- proficiência >= corte) contra a taxa oficial publicada, por nível, ano e rede.
-- Rede 5 (Pública) = redes 2 + 3. Onde falta um dos lados o valor é NULL, nunca zero.
CREATE OR REPLACE TABLE `{{ gold }}.reconciliacao`
CLUSTER BY nivel, ano AS
WITH base AS (
  SELECT id_municipio, sigla_uf, ano, rede AS rede_codigo, proficiencia, peso_aluno
  FROM `{{ silver }}.alunos` WHERE avaliado
  UNION ALL
  SELECT id_municipio, sigla_uf, ano, '5' AS rede_codigo, proficiencia, peso_aluno
  FROM `{{ silver }}.alunos` WHERE avaliado AND rede IN ('2', '3')
),
medida AS (
  SELECT 'municipio' AS nivel, id_municipio AS id_territorio, ano, rede_codigo,
    100 * SAFE_DIVIDE(SUM(IF(proficiencia >= {{ cutoff }}, peso_aluno, 0)), SUM(peso_aluno)) AS taxa_recalculada,
    COUNT(*) AS alunos_avaliados, SUM(peso_aluno) AS peso_avaliado
  FROM base GROUP BY 1, 2, 3, 4
  UNION ALL
  SELECT 'uf', sigla_uf, ano, rede_codigo,
    100 * SAFE_DIVIDE(SUM(IF(proficiencia >= {{ cutoff }}, peso_aluno, 0)), SUM(peso_aluno)),
    COUNT(*), SUM(peso_aluno)
  FROM base GROUP BY 1, 2, 3, 4
  UNION ALL
  SELECT 'brasil', 'BR', ano, rede_codigo,
    100 * SAFE_DIVIDE(SUM(IF(proficiencia >= {{ cutoff }}, peso_aluno, 0)), SUM(peso_aluno)),
    COUNT(*), SUM(peso_aluno)
  FROM base GROUP BY 1, 2, 3, 4
),
oficial AS (
  SELECT 'municipio' AS nivel, id_municipio AS id_territorio, ano, rede AS rede_codigo,
    taxa_alfabetizacao AS taxa_oficial, 'municipio' AS fonte_oficial
  FROM `{{ silver }}.municipio` WHERE serie = '2'
  UNION ALL
  SELECT 'uf', sigla_uf, ano, rede, taxa_alfabetizacao, 'uf'
  FROM `{{ silver }}.uf` WHERE serie = '2'
  UNION ALL
  SELECT 'brasil', 'BR', ano, rede_codigo, taxa_alfabetizacao, 'meta_alfabetizacao_brasil'
  FROM `{{ silver }}.meta_brasil`
)
SELECT
  COALESCE(m.nivel, o.nivel) AS nivel,
  COALESCE(m.id_territorio, o.id_territorio) AS id_territorio,
  COALESCE(m.ano, o.ano) AS ano,
  COALESCE(m.rede_codigo, o.rede_codigo) AS rede_codigo,
  o.taxa_oficial,
  m.taxa_recalculada,
  m.taxa_recalculada - o.taxa_oficial AS diferenca_pp,
  m.alunos_avaliados,
  m.peso_avaliado,
  o.fonte_oficial,
  m.taxa_recalculada IS NOT NULL AS tem_microdados,
  o.taxa_oficial IS NOT NULL AS tem_oficial
FROM medida AS m
FULL OUTER JOIN oficial AS o
  ON m.nivel = o.nivel AND m.id_territorio = o.id_territorio AND m.ano = o.ano AND m.rede_codigo = o.rede_codigo;
