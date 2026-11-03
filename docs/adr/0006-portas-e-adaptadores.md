# ADR 0006: Núcleo puro com portas e adaptadores

**Status:** aceito

**Decisão.** `ports.py` define protocolos (`Warehouse`, `MessageSource`, `MessagePublisher`). Somente `adapters/`
importa SDKs de nuvem. A CLI é a raiz de composição.

**Consequências.** Todo o fluxo (inclusive ordem commit → ack) é testado com dublês em memória, sem credenciais.
Trocar o armazenamento ou a fila exige apenas outro adaptador.
