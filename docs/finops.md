# FinOps: projeção mensal de custo

| Serviço | Unidade | Quantidade medida | Preço unitário | Custo mensal projetado |
|---|---|---|---|---:|
| BigQuery: análise (on-demand) | TiB processados/mês | 0.002626 TiB (2888 MB) projetados a partir de execuções medidas | US$ 6.25/TiB; 1 TiB/mês grátis | US$ 0.0000 |
| BigQuery: armazenamento | GiB-mês (lógico) | 0.751 ativo + 0.000 longo prazo, medidos | US$ 0.023/GiB ativo; 10 GiB/mês grátis | US$ 0.0000 |
| Cloud Storage: Bronze Parquet | GiB-mês | 0.074 GiB, medidos no bucket | US$ 0.02/GiB (us-central1); 5 GiB/mês grátis | US$ 0.0000 |
| Pub/Sub: mensagens | GiB trafegados/mês | 0.0096 GiB (volume medido x2: publicação e entrega) | US$ 40/TiB; 10 GiB/mês grátis | US$ 0.0000 |
| Cloud Run Jobs | vCPU-s e GiB-s/mês | 36998 vCPU-s e 36998 GiB-s projetados a partir de durações medidas | US$ 1.8e-05/vCPU-s e US$ 2e-06/GiB-s; franquia mensal | US$ 0.0000 |
| Cloud Scheduler | jobs agendados | 3 jobs | US$ 0.1/job; 3 grátis | US$ 0.0000 |
| **Total** | | | | **US$ 0.0000** |

Sem nenhuma franquia gratuita (pior caso), a projeção seria **US$ 1.0755/mês**.
Nos últimos 30 dias, o pipeline faturou 10420.7 MB de análise no BigQuery (todos os jobs rotulados `app=radar-alfabetizacao`).

## Premissas

- Cronograma e preços em `config/finops_prices.yaml`.
- Execução sem mudança na fonte custa só consultas de metadados e do registro operacional (mínimo de 10 MiB faturados por consulta).
- Cloud Logging e Cloud Monitoring ficam dentro da franquia gratuita no volume esperado (logs de poucos KB por execução; não medido).
