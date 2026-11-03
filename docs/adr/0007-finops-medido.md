# ADR 0007: FinOps calculado de medições

**Status:** aceito

**Decisão.** Todo job do BigQuery recebe rótulos (`app`, `run_id`, `step`). `ops.steps` guarda bytes faturados e
duração de cada etapa. `radar finops` projeta o mês com o cronograma de `config/finops_prices.yaml` e produz a
tabela Serviço / Unidade / Quantidade medida / Preço unitário / Custo mensal projetado, mais o pior caso sem franquias.

**Consequências.** A projeção muda sozinha conforme a execução real. Preços ainda não conferidos na página oficial
estão marcados com `verificado: false` e aparecem como aviso no relatório.
