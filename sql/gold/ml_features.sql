-- Fase 3 (modelo preditivo): ATRIBUTOS observados no ano de referência (t). Não contém nenhuma
-- informação do ano-alvo (t+1): o rótulo vive em ml_labels, ligado por (id_municipio, rede, ano_referencia).
-- `meta_proximo_ano` é uma meta pactuada com antecedência, portanto conhecida em t.
CREATE OR REPLACE TABLE `{{ gold }}.ml_features`
CLUSTER BY sigla_uf, ano_referencia AS
SELECT
  m.id_territorio AS id_municipio,
  m.sigla_uf,
  m.ano AS ano_referencia,
  m.rede_codigo,
  m.taxa_alfabetizacao AS taxa_referencia,
  m.meta_ano_seguinte AS meta_proximo_ano,
  m.taxa_alfabetizacao - m.meta_ano_seguinte AS distancia_para_meta_proxima_pp,
  m.percentual_participacao,
  m.nivel_alfabetizacao,
  r.media_portugues,
  r.proporcao_aluno_nivel_0, r.proporcao_aluno_nivel_1, r.proporcao_aluno_nivel_2,
  r.proporcao_aluno_nivel_3, r.proporcao_aluno_nivel_4, r.proporcao_aluno_nivel_5,
  r.proporcao_aluno_nivel_6, r.proporcao_aluno_nivel_7, r.proporcao_aluno_nivel_8,
  c.alunos_avaliados
FROM `{{ silver }}.meta_municipio` AS m
LEFT JOIN `{{ silver }}.municipio` AS r
  ON r.id_municipio = m.id_territorio AND r.ano = m.ano AND r.rede = m.rede_codigo AND r.serie = '2'
LEFT JOIN `{{ gold }}.reconciliacao` AS c
  ON c.nivel = 'municipio' AND c.id_territorio = m.id_territorio
 AND c.ano = m.ano AND c.rede_codigo = m.rede_codigo;
