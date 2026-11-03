"""Consumidor de streaming (micro-lotes).

Entrega do Pub/Sub é "pelo menos uma vez": a mesma mensagem pode chegar mais de uma vez. O
consumidor é idempotente porque a deduplicação (por `event_id`) e o MERGE no Gold acontecem na
MESMA transação do BigQuery, e a confirmação (ack) só ocorre depois do commit.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from radar_alfabetizacao.domain.eventos import Evento, validar_mensagem
from radar_alfabetizacao.logging_setup import log_event
from radar_alfabetizacao.pipeline.context import PipelineContext
from radar_alfabetizacao.ports import MessageSource, ReceivedMessage

log = logging.getLogger(__name__)

STAGING_SCHEMA: tuple[tuple[str, str], ...] = (
    ("event_id", "STRING"),
    ("source_table", "STRING"),
    ("nivel", "STRING"),
    ("id_territorio", "STRING"),
    ("sigla_uf", "STRING"),
    ("ano", "INTEGER"),
    ("rede_codigo", "STRING"),
    ("taxa_alfabetizacao", "FLOAT"),
    ("meta_ano", "FLOAT"),
    ("meta_final", "FLOAT"),
    ("percentual_participacao", "FLOAT"),
    ("origem_dado", "STRING"),
    ("source_version", "STRING"),
    ("produced_at", "TIMESTAMP"),
)


@dataclass
class ConsumerTotals:
    batches: int = 0
    pulled: int = 0
    valid: int = 0
    quarantined: int = 0
    duplicates: int = 0
    merged_new: int = 0
    latencies: list[float] = field(default_factory=list)


def percentile(values: Sequence[float], q: float) -> float | None:
    """Percentil pelo método do posto mais próximo (q entre 0 e 1); None se vazio."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(q * len(ordered)))
    return ordered[rank - 1]


def run_consumer(
    ctx: PipelineContext,
    source: MessageSource,
    *,
    max_batches: int = 20,
    batch_size: int = 1000,
) -> ConsumerTotals:
    ctx.recorder.start("consume", {"max_batches": max_batches, "batch_size": batch_size})
    try:
        ctx.ensure_schema()
        totals = _loop(ctx, source, max_batches, batch_size)
    except Exception as exc:
        ctx.recorder.finish("failed", error=f"{type(exc).__name__}: {exc}")
        log_event(
            log,
            "run_failed",
            f"consumidor falhou: {exc}",
            level=logging.ERROR,
            run_id=ctx.run_id,
            command="consume",
            error_type=type(exc).__name__,
        )
        ctx.recorder.safe_flush()
        raise
    ctx.recorder.finish("succeeded")
    ctx.recorder.flush()
    log_event(
        log,
        "run_succeeded",
        f"consumidor concluído: {totals.merged_new} novos eventos integrados",
        run_id=ctx.run_id,
        command="consume",
        pulled=totals.pulled,
        quarantined=totals.quarantined,
        duplicates=totals.duplicates,
    )
    return totals


def _loop(
    ctx: PipelineContext, source: MessageSource, max_batches: int, batch_size: int
) -> ConsumerTotals:
    totals = ConsumerTotals()
    for number in range(1, max_batches + 1):
        messages = source.pull(batch_size)
        if not messages:
            break
        _process_batch(ctx, source, messages, f"{ctx.run_id}-b{number}", totals)
        totals.batches += 1
    return totals


def _process_batch(
    ctx: PipelineContext,
    source: MessageSource,
    messages: list[ReceivedMessage],
    batch_id: str,
    totals: ConsumerTotals,
) -> None:
    started = ctx.clock()
    received_at = started
    valid: list[tuple[ReceivedMessage, Evento]] = []
    raw_rows: list[dict[str, Any]] = []
    quarantined = 0
    for message in messages:
        outcome = validar_mensagem(message.data, ctx.contract, received_at)
        raw_rows.append(_raw_row(message, outcome.evento, outcome.motivos, batch_id, received_at))
        if outcome.evento is None:
            quarantined += 1
        else:
            valid.append((message, outcome.evento))

    unicos: dict[str, Evento] = {}
    for _, evento in valid:
        unicos.setdefault(evento.event_id, evento)
    duplicates_in_batch = len(valid) - len(unicos)

    ctx.warehouse.load_rows(f"{ctx.settings.bronze}.stream_events", raw_rows, step="stream.bronze")

    duplicates_ledger = 0
    merged_new = 0
    if unicos:
        staging = f"{ctx.settings.ops}.stg_{_safe_id(batch_id)}"
        ctx.warehouse.load_rows(
            staging,
            [_staging_row(e) for e in unicos.values()],
            step="stream.staging",
            schema=STAGING_SCHEMA,
            ttl_hours=24,
            truncate=True,
        )
        known = ctx.run_sql(
            "stream/duplicados_no_ledger.sql", step="stream.ledger_check", staging=staging
        )
        duplicates_ledger = int(known.rows[0]["observed"]) if known.rows else 0
        ctx.run_sql(
            "silver/stream_commit.sql",
            step="stream.commit",
            params={"run_id": ctx.run_id, "batch_id": batch_id},
            staging=staging,
            source_template="gold/termometro_source_stream.sql",
        )
        merged_new = len(unicos) - duplicates_ledger

    source.ack([m.ack_id for m in messages])  # só depois do commit: falha antes = reentrega

    latencies = [(received_at - m.publish_time).total_seconds() for m, _ in valid]
    duration = (ctx.clock() - started).total_seconds()
    ctx.warehouse.load_rows(
        f"{ctx.settings.ops}.stream_batches",
        [
            {
                "batch_id": batch_id,
                "run_id": ctx.run_id,
                "pulled": len(messages),
                "valid": len(valid),
                "quarantined": quarantined,
                "duplicates_in_batch": duplicates_in_batch,
                "duplicates_ledger": duplicates_ledger,
                "merged_new": merged_new,
                "latency_p50_seconds": percentile(latencies, 0.50),
                "latency_p95_seconds": percentile(latencies, 0.95),
                "duration_seconds": round(duration, 3),
                "status": "partial" if quarantined else "ok",
                "recorded_at": ctx.clock().isoformat(),
            }
        ],
        step="stream.batches",
    )
    totals.pulled += len(messages)
    totals.valid += len(valid)
    totals.quarantined += quarantined
    totals.duplicates += duplicates_in_batch + duplicates_ledger
    totals.merged_new += merged_new
    totals.latencies.extend(latencies)
    log_event(
        log,
        "stream_batch",
        f"lote {batch_id}: {len(messages)} recebidas, {quarantined} em quarentena",
        run_id=ctx.run_id,
        batch_id=batch_id,
        merged_new=merged_new,
    )


def _safe_id(batch_id: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in batch_id).lower()


def _staging_row(evento: Evento) -> dict[str, Any]:
    row = evento.model_dump(mode="json")
    return {name: row[name] for name, _ in STAGING_SCHEMA}


def _raw_row(
    message: ReceivedMessage,
    evento: Evento | None,
    motivos: Sequence[str],
    batch_id: str,
    received_at: datetime,
) -> dict[str, Any]:
    return {
        "message_id": message.message_id,
        "event_id": evento.event_id if evento else None,
        "payload": message.data.decode("utf-8", errors="replace"),
        "publish_time": message.publish_time.isoformat(),
        "received_at": received_at.isoformat(),
        "batch_id": batch_id,
        "valid": evento is not None,
        "reasons": "; ".join(motivos) if motivos else None,
    }
