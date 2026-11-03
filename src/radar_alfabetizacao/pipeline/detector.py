"""Detector de mudanças: transforma atualizações REAIS da fonte oficial em eventos no Pub/Sub.

Para cada tabela vigiada, compara a versão da fonte (metadados) com a última já publicada. Se
mudou, lê as linhas, converte em eventos e publica apenas os que ainda não foram integrados.
Nenhum dado é inventado: cada evento é uma linha publicada pelo INEP.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from radar_alfabetizacao.domain.eventos import construir_evento
from radar_alfabetizacao.logging_setup import log_event
from radar_alfabetizacao.pipeline.context import PipelineContext, source_version
from radar_alfabetizacao.ports import MessagePublisher

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DetectorResult:
    published: int
    tables_changed: list[str]
    tables_unchanged: list[str]


def run_detector(
    ctx: PipelineContext, publisher: MessagePublisher, *, force: bool = False
) -> DetectorResult:
    ctx.recorder.start("detect", {"force": force})
    try:
        result = _execute(ctx, publisher, force=force)
    except Exception as exc:
        ctx.recorder.finish("failed", error=f"{type(exc).__name__}: {exc}")
        log_event(
            log,
            "run_failed",
            f"detector falhou: {exc}",
            level=logging.ERROR,
            run_id=ctx.run_id,
            command="detect",
            error_type=type(exc).__name__,
        )
        ctx.recorder.safe_flush()
        raise
    ctx.recorder.finish("succeeded")
    ctx.recorder.flush()
    log_event(
        log,
        "run_succeeded",
        f"detector concluído: {result.published} eventos publicados",
        run_id=ctx.run_id,
        command="detect",
        published=result.published,
    )
    return result


def _execute(ctx: PipelineContext, publisher: MessagePublisher, *, force: bool) -> DetectorResult:
    ctx.ensure_schema()
    src = ctx.contract.source_dataset
    last = ctx.processed_versions("stream")
    published = 0
    changed: list[str] = []
    unchanged: list[str] = []
    for table in ctx.contract.watch_tables:
        info = ctx.warehouse.table_info(f"{src}.{table}")
        version = source_version(info)
        if version == last.get(table) and not force:
            unchanged.append(table)
            ctx.recorder.step(f"detect.{table}", detail="sem mudança na fonte")
            continue
        rows = ctx.run_sql("stream/fonte.sql", step=f"detect.read.{table}", table=table).rows
        known = {
            r["event_id"]
            for r in ctx.run_sql(
                "stream/eventos_conhecidos.sql",
                step=f"detect.known.{table}",
                params={"table": table},
            ).rows
        }
        events = [
            construir_evento(
                table, row, ctx.contract, source_version=version, produced_at=info.modified_at
            )
            for row in rows
        ]
        novos = [e for e in events if e.event_id not in known]
        publisher.publish_all(
            [(e.to_message(), {"event_id": e.event_id, "origem": e.origem_dado}) for e in novos]
        )
        ctx.record_versions("stream", {table: info}, {table: version})
        ctx.recorder.step(
            f"detect.{table}", detail=f"{len(novos)} novos de {len(events)} linhas lidas"
        )
        published += len(novos)
        changed.append(table)
    return DetectorResult(published, changed, unchanged)
