# ADR 0008: Cloud Run Jobs + Cloud Scheduler

**Status:** aceito

**Contexto.** O volume é pequeno (milhões de linhas, uma atualização da fonte a cada poucos meses).

**Decisão.** Três Cloud Run Jobs (batch, detect, consume) disparados pelo Scheduler. Sem Composer (custo fixo
mensal) nem Dataflow (excessivo para micro-lotes de milhares de mensagens). O processamento pesado é SQL no BigQuery.

**Consequências.** Custo próximo de zero e operação simples. Se o volume crescer, o consumidor pode migrar para um
serviço sempre ligado sem mudar o núcleo.
