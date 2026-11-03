"""Pipeline batch: fonte oficial no BigQuery -> Bronze -> Silver -> Gold, com gates de qualidade.

Idempotência: uma tabela só gera nova versão Bronze quando a fonte mudou. Sem mudança, a execução
termina sem custo relevante. As versões só são marcadas como "processadas" depois que Silver e
Gold passam nos gates; uma falha no meio é refeita na execução seguinte.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass

from radar_alfabetizacao.contract import Severity, ddl_type, meta_years
from radar_alfabetizacao.logging_setup import log_event
from radar_alfabetizacao.pipeline.context import PipelineContext, source_version
from radar_alfabetizacao.pipeline.specs import META_SILVER, RESULTADO_SILVER
from radar_alfabetizacao.ports import TableInfo
from radar_alfabetizacao.quality.contract_gate import schema_results
from radar_alfabetizacao.quality.engine import RuleResult

log = logging.getLogger(__name__)

SKIPPED = "skipped_no_changes"
SUCCEEDED = "succeeded"

DEMO_FAILURE = RuleResult(
    rule_id="demo.falha_injetada",
    layer="silver",
    severity=Severity.BLOCKING,
    passed=False,
    observed=1.0,
    expectation="== 0",
    message="Falha injetada de propósito para demonstrar o bloqueio e o alerta",
)


@dataclass(frozen=True)
class BatchResult:
    status: str
    versions: dict[str, str]
    changed: list[str]


def run_batch(
    ctx: PipelineContext, *, force: bool = False, demo_gate_failure: bool = False
) -> BatchResult:
    ctx.recorder.start("batch", {"force": force, "demo_gate_failure": demo_gate_failure})
    try:
        result = _execute(ctx, force=force, demo_gate_failure=demo_gate_failure)
    except Exception as exc:
        ctx.recorder.finish("failed", error=f"{type(exc).__name__}: {exc}")
        log_event(
            log,
            "run_failed",
            f"batch falhou: {exc}",
            level=logging.ERROR,
            run_id=ctx.run_id,
            command="batch",
            error_type=type(exc).__name__,
        )
        ctx.recorder.safe_flush()
        raise
    ctx.recorder.finish("succeeded")
    ctx.recorder.flush()
    log_event(
        log,
        "run_succeeded",
        f"batch concluído: {result.status}",
        run_id=ctx.run_id,
        command="batch",
        changed=result.changed,
    )
    return result


def _execute(ctx: PipelineContext, *, force: bool, demo_gate_failure: bool) -> BatchResult:
    force = force or demo_gate_failure  # a demonstração só faz sentido se o Silver for reconstruído
    ctx.ensure_schema()
    src = ctx.contract.source_dataset
    infos = {t: ctx.warehouse.table_info(f"{src}.{t}") for t in ctx.contract.tables}
    versions = {t: source_version(i) for t, i in infos.items()}

    ctx.gate.run(
        "contract", ctx.sql_context(), extra=schema_results(ctx.contract, infos, ctx.clock())
    )

    processed = ctx.processed_versions("batch")
    changed = [t for t in versions if versions[t] != processed.get(t)]
    if not changed and not force:
        ctx.recorder.step("batch.sem_mudancas", detail="fonte inalterada desde a última execução")
        return BatchResult(SKIPPED, versions, [])

    for table in changed if not force else list(versions):
        _ingest_bronze(ctx, table, versions[table], infos[table])
    source_rows = {t: i.num_rows for t, i in infos.items()}
    ctx.gate.run("bronze", ctx.sql_context(versions=versions, source_rows=source_rows))

    _build_silver(ctx, versions, infos)
    extra = [DEMO_FAILURE] if demo_gate_failure else []
    ctx.gate.run("silver", ctx.sql_context(versions=versions), extra=extra)

    _build_gold(ctx, versions, infos)
    ctx.gate.run("gold", ctx.sql_context(versions=versions))

    done = {t: versions[t] for t in (versions if force else changed)}
    ctx.record_versions("batch", infos, done)
    return BatchResult(SUCCEEDED, versions, changed)


def _ingest_bronze(ctx: PipelineContext, table: str, version: str, info: TableInfo) -> None:
    ctx.run_sql(
        "bronze/ingest_version.sql",
        step=f"bronze.{table}",
        params={"run_id": ctx.run_id, "source_version": version},
        table=table,
        columns={name: ddl_type(kind) for name, kind in info.columns.items()},
    )
    ctx.run_sql(
        "bronze/export_parquet.sql", step=f"bronze.export.{table}", table=table, version=version
    )


def _build_silver(
    ctx: PipelineContext, versions: Mapping[str, str], infos: Mapping[str, TableInfo]
) -> None:
    ctx.run_sql("silver/ref_uf.sql", step="silver.ref_uf")
    ctx.run_sql("silver/dicionario.sql", step="silver.dicionario", versions=versions)
    ctx.run_sql("silver/alunos.sql", step="silver.alunos", versions=versions)
    for table, derive_uf in RESULTADO_SILVER:
        ctx.run_sql(
            "silver/resultado.sql",
            step=f"silver.{table}",
            table=table,
            derive_uf=derive_uf,
            versions=versions,
        )
    for spec in META_SILVER:
        ctx.run_sql(
            "silver/meta.sql",
            step=f"silver.{spec.target}",
            spec=spec,
            years=meta_years(infos[spec.source].columns),
            versions=versions,
        )


def _build_gold(
    ctx: PipelineContext, versions: Mapping[str, str], infos: Mapping[str, TableInfo]
) -> None:
    batch_sources = [
        {
            "nivel": s.nivel,
            "table": s.target,
            "version": versions[s.source],
            "modified": infos[s.source].modified_at.isoformat(sep=" "),
        }
        for s in META_SILVER
    ]
    ctx.run_sql("gold/reconciliacao.sql", step="gold.reconciliacao")
    ctx.run_sql(
        "gold/termometro_merge.sql",
        step="gold.termometro",
        params={"run_id": ctx.run_id},
        source_template="gold/termometro_source_batch.sql",
        batch_sources=batch_sources,
    )
    ctx.run_sql("gold/indicador_municipal.sql", step="gold.indicador_municipal")
    ctx.run_sql("gold/ml_features.sql", step="gold.ml_features")
    ctx.run_sql("gold/ml_labels.sql", step="gold.ml_labels")
