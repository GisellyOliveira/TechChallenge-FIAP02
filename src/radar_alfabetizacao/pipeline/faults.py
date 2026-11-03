"""Injeção controlada de falhas, para demonstrar deduplicação e quarentena no streaming.

Somente mensagens INVÁLIDAS ou DUPLICADAS são injetadas, sempre com atributo origem=simulado.
Nenhum evento simulado válido entra no Gold.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

from radar_alfabetizacao.domain.eventos import Evento

SIMULADO = {"origem": "simulado"}


def build_fault_messages(real: Evento) -> list[tuple[bytes, Mapping[str, str]]]:
    """Monta mensagens defeituosas a partir de um evento real já publicado."""
    base = real.model_dump(mode="json")
    amanha = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    defeituosos: list[dict[str, object]] = [
        {k: v for k, v in base.items() if k != "taxa_alfabetizacao" and k != "ano"},
        {**base, "taxa_alfabetizacao": 140.0},
        {**base, "rede_codigo": "9"},
        {**base, "produced_at": amanha},
        {**base, "id_territorio": "XX", "nivel": "uf"},
    ]
    messages: list[tuple[bytes, Mapping[str, str]]] = [
        (real.to_message(), SIMULADO),
        (real.to_message(), SIMULADO),  # duplicata do evento real
    ]
    for payload in defeituosos:
        payload = {**payload, "origem_dado": "simulado"}
        messages.append((json.dumps(payload).encode("utf-8"), SIMULADO))
    messages.append((b"isto nao e json", SIMULADO))
    return messages
