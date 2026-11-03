# ADR 0005: Qualidade como regras SQL declarativas

**Status:** aceito

**Decisão.** Cada regra é um SQL que devolve `observed`, com operador e valor esperado, em `config/rules.yaml`.
Severidade `blocking` impede a camada seguinte; `informative` só registra. O motor roda todas as regras da camada,
**persiste os resultados** e só então levanta `QualityGateError`. Regra que falha ao executar conta como reprovada.

**Limiares.** Taxas de *join* bloqueiam abaixo de 0,90, com justificativa no arquivo.

**Consequências.** Adicionar regra não exige código. A evidência de uma execução reprovada existe e é consultável.
