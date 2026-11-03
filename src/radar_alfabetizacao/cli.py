"""Interface de linha de comando (raiz de composição: cria adaptadores e liga o núcleo a eles)."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Callable, Sequence
from pathlib import Path

from pydantic import ValidationError

from radar_alfabetizacao.logging_setup import configure_logging
from radar_alfabetizacao.ops.docs import replace_block
from radar_alfabetizacao.pipeline.context import PipelineContext, new_run_id
from radar_alfabetizacao.settings import Settings

log = logging.getLogger(__name__)


def _context(settings: Settings) -> PipelineContext:
    from google.cloud import bigquery

    from radar_alfabetizacao.adapters.bigquery import BigQueryGateway
    from radar_alfabetizacao.contract import load_contract, load_rules

    run_id = new_run_id()
    warehouse = BigQueryGateway(
        bigquery.Client(project=settings.project_id), location=settings.location, run_id=run_id
    )
    return PipelineContext.build(
        settings,
        load_contract(settings.config_dir / "sources.yaml"),
        load_rules(settings.config_dir / "rules.yaml"),
        warehouse,
        run_id,
    )


def _cmd_init(settings: Settings, args: argparse.Namespace) -> int:
    ctx = _context(settings)
    ctx.ensure_schema()
    print(f"Esquema operacional pronto em {settings.ops} (run_id={ctx.run_id}).")
    return 0


def _cmd_batch(settings: Settings, args: argparse.Namespace) -> int:
    from radar_alfabetizacao.pipeline.batch import run_batch

    result = run_batch(
        _context(settings),
        force=args.force or args.demo_gate_failure,
        demo_gate_failure=args.demo_gate_failure,
    )
    print(f"batch: {result.status}; tabelas alteradas: {result.changed or 'nenhuma'}")
    return 0


def _cmd_detect(settings: Settings, args: argparse.Namespace) -> int:
    from radar_alfabetizacao.adapters.pubsub import PubSubPublisher
    from radar_alfabetizacao.pipeline.detector import run_detector

    publisher = PubSubPublisher(settings.project_id, settings.pubsub_topic)
    result = run_detector(_context(settings), publisher, force=args.force)
    print(f"detect: {result.published} eventos publicados; alteradas: {result.tables_changed}")
    return 0


def _cmd_consume(settings: Settings, args: argparse.Namespace) -> int:
    from radar_alfabetizacao.adapters.pubsub import PubSubPuller
    from radar_alfabetizacao.pipeline.consumer import run_consumer

    puller = PubSubPuller(settings.project_id, settings.pubsub_subscription)
    totals = run_consumer(_context(settings), puller, max_batches=args.max_batches)
    print(
        f"consume: {totals.pulled} recebidas, {totals.merged_new} integradas, "
        f"{totals.quarantined} em quarentena, {totals.duplicates} duplicadas"
    )
    return 0


def _cmd_inject_faults(settings: Settings, args: argparse.Namespace) -> int:
    from radar_alfabetizacao.adapters.pubsub import PubSubPublisher
    from radar_alfabetizacao.domain.eventos import construir_evento
    from radar_alfabetizacao.pipeline.context import source_version
    from radar_alfabetizacao.pipeline.faults import build_fault_messages

    ctx = _context(settings)
    table = "meta_alfabetizacao_brasil"
    info = ctx.warehouse.table_info(f"{ctx.contract.source_dataset}.{table}")
    rows = ctx.run_sql("stream/fonte.sql", step="faults.read", table=table).rows
    real = construir_evento(
        table,
        sorted(rows, key=lambda r: r["ano"])[-1],
        ctx.contract,
        source_version=source_version(info),
        produced_at=info.modified_at,
    )
    messages = build_fault_messages(real)
    PubSubPublisher(settings.project_id, settings.pubsub_topic).publish_all(messages)
    print(
        f"{len(messages)} mensagens defeituosas publicadas (origem=simulado). Rode `radar consume`."
    )
    return 0


def _cmd_finops(settings: Settings, args: argparse.Namespace) -> int:
    from radar_alfabetizacao.adapters.storage import bucket_size_bytes
    from radar_alfabetizacao.ops.finops import (
        collect_measurements,
        load_prices,
        project,
        render_markdown,
    )

    ctx = _context(settings)
    prices = load_prices(settings.config_dir / "finops_prices.yaml")
    measurements = collect_measurements(
        ctx, gcs_bytes=bucket_size_bytes(settings.project_id, settings.bucket), days=args.days
    )
    markdown = render_markdown(
        project(measurements, prices), measurements.total_bytes_faturados, args.days
    )
    Path(args.output).write_text(markdown, encoding="utf-8")
    print(f"FinOps gravado em {args.output}")
    if args.readme:
        readme = Path(args.readme)
        table = markdown.split("## Premissas")[0].replace("# FinOps: projeção mensal de custo", "")
        readme.write_text(
            replace_block(readme.read_text(encoding="utf-8"), "FINOPS", table), encoding="utf-8"
        )
        print(f"Tabela FinOps atualizada em {args.readme}")
    return 0


def _cmd_evidence(settings: Settings, args: argparse.Namespace) -> int:
    from radar_alfabetizacao.ops.evidence import build_report

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(build_report(_context(settings)), encoding="utf-8")
    print(f"Evidências gravadas em {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="radar", description="Radar da Alfabetização")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="cria o esquema operacional (idempotente)")

    batch = sub.add_parser("batch", help="Bronze -> Silver -> Gold a partir da fonte oficial")
    batch.add_argument("--force", action="store_true", help="reprocessa mesmo sem mudança na fonte")
    batch.add_argument(
        "--demo-gate-failure",
        action="store_true",
        help="injeta uma regra bloqueante reprovada para demonstrar o bloqueio e o alerta",
    )

    detect = sub.add_parser("detect", help="publica no Pub/Sub as atualizações reais da fonte")
    detect.add_argument("--force", action="store_true", help="relê as tabelas mesmo sem mudança")

    consume = sub.add_parser("consume", help="consome eventos em micro-lotes e faz MERGE no Gold")
    consume.add_argument("--max-batches", type=int, default=50)

    sub.add_parser("inject-faults", help="publica mensagens defeituosas (origem=simulado)")

    finops = sub.add_parser("finops", help="gera a projeção FinOps com valores medidos")
    finops.add_argument("--days", type=int, default=30)
    finops.add_argument("--output", default="docs/finops.md")
    finops.add_argument("--readme", help="README cujo bloco FINOPS será atualizado")

    evidence = sub.add_parser("evidence", help="gera o relatório de evidências de execução")
    evidence.add_argument("--output", default="docs/execucao-cloud/evidencias.md")
    return parser


_COMMANDS: dict[str, Callable[[Settings, argparse.Namespace], int]] = {
    "init": _cmd_init,
    "batch": _cmd_batch,
    "detect": _cmd_detect,
    "consume": _cmd_consume,
    "inject-faults": _cmd_inject_faults,
    "finops": _cmd_finops,
    "evidence": _cmd_evidence,
}


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = Settings()  # campos obrigatórios vêm do ambiente
    except ValidationError:
        print("Configuração ausente: defina RADAR_PROJECT_ID e RADAR_BUCKET (veja .env.example).")
        return 2
    configure_logging(settings.log_level)
    try:
        return _COMMANDS[args.command](settings, args)
    except Exception:
        log.exception("comando falhou", extra={"command": args.command})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
