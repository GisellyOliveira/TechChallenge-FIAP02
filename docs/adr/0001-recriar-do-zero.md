# ADR 0001: Recriar o projeto do zero

**Status:** aceito

**Contexto.** Havia um esboço anterior do desafio com a lógica de cálculo correta, mas sem
separação de camadas, sem testes, com estado e credenciais acoplados ao código e sem evidência de execução na nuvem.

**Decisão.** Novo repositório com estrutura própria. Aproveitamos apenas a lógica do cálculo, os casos de
conferência (Iguatu/CE e São Paulo/2023), ideias de SQL e as lições de documentação.

**Consequências.** Mais trabalho inicial; em troca, cada requisito do desafio tem um ponto de entrada claro,
testes desde o começo e nenhuma dívida herdada.
