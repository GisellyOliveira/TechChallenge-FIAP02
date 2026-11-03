# ADR 0010: Tudo na região US

**Status:** aceito

**Decisão.** Datasets do BigQuery em `US` (mesma localização da fonte pública, requisito para consultas e
junções sem cópia). Cloud Run, Artifact Registry e bucket em `us-central1`, que está dentro do multirregião US
(exportação do BigQuery para o bucket é permitida).

**Consequências.** Sem custo de transferência entre regiões e sem cópia da fonte.
