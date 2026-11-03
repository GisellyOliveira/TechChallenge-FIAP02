# ADR 0003: Streaming real, idempotente, com ack após o commit

**Status:** aceito

**Contexto.** O desafio pede ingestão híbrida, e a regra do projeto é não usar dado inventado.

**Decisão.** O evento é uma linha **oficial** das tabelas de meta (`meta_alfabetizacao_brasil/uf/municipio`),
publicada quando a fonte muda. `event_id` = hash do conteúdo. O consumidor valida, grava tudo na Bronze de streaming,
e integra as válidas numa transação (livro-razão + `MERGE`). O `ack` ocorre depois do commit.

**Falhas injetadas.** `radar inject-faults` publica somente mensagens inválidas ou duplicadas, com `origem=simulado`.

**Consequências.** Falha antes do commit gera reentrega sem perda nem duplicação. Latência medida é a do pipeline
(não a da fonte). A DLQ (5 tentativas) impede mensagem venenosa em laço.
