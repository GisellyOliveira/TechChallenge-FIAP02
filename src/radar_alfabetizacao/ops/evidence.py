"""Evidências de execução: lê as tabelas `ops.*` e gera o relatório em Markdown.

O relatório reúne o que o desafio pede como prova: job IDs, linhas, bytes, resultados de
qualidade (inclusive reprovados), lotes de streaming e contagem de linhas por tabela.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from radar_alfabetizacao.pipeline.context import PipelineContext

_SECTIONS: tuple[tuple[str, str], ...] = (
    ("Execuções recentes", "ops/evidencia_execucoes.sql"),
    ("Jobs do BigQuery (job_id, linhas e bytes faturados)", "ops/evidencia_jobs.sql"),
    ("Qualidade por execução e camada", "ops/evidencia_qualidade.sql"),
    ("Regras reprovadas", "ops/evidencia_reprovadas.sql"),
    ("Lotes de streaming", "ops/evidencia_streaming.sql"),
    ("Linhas por tabela", "ops/evidencia_tabelas.sql"),
)


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value).replace("|", "\\|").replace("\n", " ")


def rows_to_markdown(rows: Sequence[dict[str, Any]]) -> str:
    if not rows:
        return "_Sem registros._"
    columns = list(rows[0])
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    lines += ["| " + " | ".join(_cell(r.get(c)) for c in columns) + " |" for r in rows]
    return "\n".join(lines)


def build_report(ctx: PipelineContext) -> str:
    s = ctx.settings
    datasets = [s.bronze_dataset, s.silver_dataset, s.gold_dataset, s.ops_dataset]
    parts = [
        "# Evidências de execução na nuvem",
        "",
        f"Gerado em {datetime.now(UTC).isoformat(timespec='seconds')} por `radar evidence`, "
        "a partir das tabelas operacionais do BigQuery (`alfabetizacao_ops`).",
        "",
    ]
    for title, template in _SECTIONS:
        rows = ctx.run_sql(
            template, step=f"evidence.{template}", datasets=datasets, project=s.project_id
        ).rows
        parts += [f"## {title}", "", rows_to_markdown(rows), ""]
    return "\n".join(parts)
