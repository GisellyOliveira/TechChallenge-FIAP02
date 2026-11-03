-- Dicionário oficial de códigos (id_tabela, nome_coluna, chave -> descrição).
CREATE OR REPLACE TABLE `{{ silver }}.dicionario` AS
SELECT id_tabela, nome_coluna, chave, valor AS descricao
FROM `{{ bronze }}.dicionario`
WHERE _source_version = '{{ versions['dicionario'] }}';
