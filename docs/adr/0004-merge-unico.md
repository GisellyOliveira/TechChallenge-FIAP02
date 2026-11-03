# ADR 0004: Um único MERGE para lote e streaming

**Status:** aceito

**Decisão.** `termometro_merge.sql` recebe o *template* de origem por parâmetro. Atualiza uma linha somente se
`produced_at` for maior ou igual ao da linha atual **e** algum valor mudou. O status vem da macro `status_expr`.

**Consequências.** Regra de status em um só lugar, com teste de paridade SQL × Python (DuckDB). Eventos fora de
ordem não regridem o Gold.
