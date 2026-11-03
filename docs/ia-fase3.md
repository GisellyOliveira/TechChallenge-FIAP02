# Preparação para a Fase 3 (modelo preditivo)

**Pergunta de modelagem:** dado o que se sabe de um município/rede no ano *t*, ele **atingirá a meta** no ano *t+1*?

## Tabelas

| Tabela | Conteúdo | Chave |
|---|---|---|
| `gold.ml_features` | Atributos observados em *t*: taxa, meta do ano seguinte (pactuada antes), distância até ela, participação, nível, média de português, proporção de alunos por nível (0 a 8) e alunos avaliados | `(id_municipio, rede_codigo, ano_referencia)` |
| `gold.ml_labels` | Alvo de *t+1*: `atingiu_meta_alvo`, `taxa_alvo`, `split_sugerido` | `(id_municipio, rede_codigo, ano_alvo)` com `ano_referencia = ano_alvo − 1` |

Junte-as por `(id_municipio, rede_codigo, ano_referencia)`.

## Como evitar vazamento do alvo

1. Nenhuma coluna de `ml_features` carrega informação do ano-alvo. A regra bloqueante `gold.ml.sem_vazamento_temporal` verifica que cada par atributo/rótulo respeita `ano_referencia = ano_alvo − 1`.
2. `split_sugerido` é **temporal**: quando houver mais de um ano-alvo, o mais recente vira teste. Não use partição aleatória.
3. `taxa_alvo` e o status do Termômetro de *t+1* pertencem ao alvo: nunca os use como feature. Se quiser sinais de anomalia (`gold.indicador_municipal`), junte-os por `ano = ano_referencia`, nunca pelo ano-alvo.
4. Aplique ajustes (normalização, seleção) só no treino.

## Limitação atual

Existe **uma** transição observável (2023 → 2024). Com isso, qualquer métrica de generalização é frágil: declarar
o tamanho do conjunto, preferir modelos simples e validar por UF (validação agrupada) em vez de sorteio aleatório.
Quando 2025 chegar à fonte, o pipeline gera a segunda transição automaticamente.
