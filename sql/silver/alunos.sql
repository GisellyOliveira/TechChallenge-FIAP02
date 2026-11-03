-- Microdados do Saeb limpos e integrados: UF derivada do IBGE, rede descrita pelo dicionário e a
-- marca `avaliado` (presente com prova preenchida). Nulos são preservados, nunca viram zero.
CREATE OR REPLACE TABLE `{{ silver }}.alunos`
CLUSTER BY ano, id_municipio AS
SELECT
  b.ano,
  b.id_municipio,
  b.id_escola,
  b.id_aluno,
  b.caderno,
  b.serie,
  b.rede,
  b.presenca,
  b.preenchimento_caderno,
  b.alfabetizado,
  b.proficiencia,
  b.peso_aluno,
  u.sigla_uf,
  COALESCE(d.descricao, 'desconhecido') AS rede_nome,
  COALESCE(b.presenca = '1' AND b.preenchimento_caderno = '1', FALSE) AS avaliado
FROM `{{ bronze }}.alunos` AS b
LEFT JOIN `{{ silver }}.ref_uf` AS u ON u.codigo_ibge = LEFT(b.id_municipio, 2)
LEFT JOIN `{{ silver }}.dicionario` AS d
  ON d.id_tabela = 'alunos' AND d.nome_coluna = 'rede' AND d.chave = b.rede
WHERE b._source_version = '{{ versions['alunos'] }}';
