# ADR 0002: Bronze append-only versionada pela fonte

**Status:** aceito

**Contexto.** A fonte é uma tabela nativa do BigQuery que o INEP/Base dos Dados substitui quando há dado novo.

**Decisão.** `source_version = sha1(última modificação | linhas | bytes)[:12]`. Uma versão nova só entra na Bronze se
ainda não existir (`INSERT ... WHERE NOT EXISTS`). Cada versão também é exportada em Parquet/Snappy para o
Cloud Storage. Colunas novas da fonte são absorvidas (um `ALTER` e `INSERT` por nome).

**Alternativas.** Truncar e recarregar (perde histórico e auditoria); particionar por data de ingestão (duplica dados
idênticos a cada execução).

**Consequências.** Execução sem mudança na fonte custa apenas consultas de metadados. A Silver lê sempre a versão
vigente. O histórico fica disponível para auditoria.
