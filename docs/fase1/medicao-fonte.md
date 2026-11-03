# Medição da fonte oficial

Fonte: `basedosdados.br_inep_avaliacao_alfabetizacao` (BigQuery, região US). Todas as tabelas são **nativas**, então
`lastModified`, linhas e bytes dos metadados são confiáveis para versionar a fonte.

## Tabelas

| Tabela | Linhas | Anos | Modificada em |
|---|---:|---|---|
| `alunos` | 3.867.999 | 2023 (1.747.439) e 2024 (2.120.560) | 14/01/2026 |
| `municipio` | 23.995 | 2023–2024 | 14/01/2026 |
| `uf` | 145 | 2023–2024 | 14/01/2026 |
| `meta_alfabetizacao_municipio` | 10.704 (5.352 por ano) | 2023–2024 | 14/01/2026 |
| `meta_alfabetizacao_uf` | 81 | até 2025 | 24/03/2026 |
| `meta_alfabetizacao_brasil` | 3 | até 2025 | 24/03/2026 |
| `dicionario` | — | — | 14/01/2026 |

O último ano é descoberto **por tabela** (`MAX(ano)`), nunca fixado no código.

## Schemas relevantes

* `alunos`: `ano`, `id_municipio`, `id_escola`, `id_aluno`, `caderno`, `serie`, `rede`, `presenca`,
  `preenchimento_caderno`, `alfabetizado` (STRING), `proficiencia` (FLOAT), `peso_aluno` (FLOAT).
* `municipio` / `uf`: `ano`, `id_municipio` ou `sigla_uf`, `serie`, `rede`, `taxa_alfabetizacao`, `media_portugues`,
  `proporcao_aluno_nivel_0..8`.
* Tabelas de meta: **sem** `serie`; `ano`, território, `rede` (**texto**), `taxa_alfabetizacao`,
  `meta_alfabetizacao_2024..2030`, `percentual_participacao` (município também traz `nivel_alfabetizacao`).

## Códigos (do dicionário oficial)

* `alunos.rede`: 1 Federal, 2 Estadual, 3 Municipal, 4 Privada.
* `municipio`/`uf`.`rede`: 0 Total, 1–4 como acima, 5 Pública (Estadual + Municipal), 6 Pública (Federal + Estadual + Municipal).
* Metas: `rede` em texto; o contrato mapeia `Pública` → `5` e `Municipal` → `3`. Texto não mapeado bloqueia.

## Combinações rede × ano

| Tabela | 2023 | 2024 |
|---|---|---|
| `alunos` | 2, 3 | 2, 3, 4 |
| `municipio` | 2, 3, 5 | 0, 2, 3, 5 |
| `uf` | 2, 3, 5 | 0, 2, 3, 5 (rede 0 em 1 UF) |

## Custo de leitura

Varredura completa de `alunos`: ~256 MiB (só a coluna `ano`: ~29,5 MiB). O BigQuery fatura no mínimo 10 MiB por
consulta. Toda a exploração inicial somou ~352 MiB faturados (0,03% da franquia mensal de 1 TiB).

## Indicador

Criança Alfabetizada = proporção de alunos avaliados com proficiência ≥ **743** (Saeb). Meta pública para 2030: **80**.
Avaliado = `presenca = '1'` e `preenchimento_caderno = '1'`. Taxa ponderada por `peso_aluno`.
