# ADR 0009: Features e rótulos da Fase 3 em tabelas separadas

**Status:** aceito

**Decisão.** `ml_features` guarda o que é conhecido no ano de referência *t*. `ml_labels` guarda o resultado do ano
*t+1* e um `split_sugerido` temporal. A regra bloqueante `gold.ml.sem_vazamento_temporal` falha se algum par
atributo/rótulo violar `ano_referencia = ano_alvo − 1`. As colunas de `ml_features` são escolhidas para conter
só informação de *t*; a regra protege a chave temporal, não o uso indevido de colunas fora desta tabela.

**Consequências.** O vazamento do alvo é barrado antes de existir modelo. Com uma única transição observável hoje
(2023 → 2024), a Fase 3 deve declarar o tamanho do conjunto e evitar conclusões de generalização.
