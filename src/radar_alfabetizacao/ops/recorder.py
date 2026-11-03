"""Registro de execuções, etapas e resultados de qualidade nas tabelas `ops.*` do BigQuery.

O registro é em memória e descarregado por `flush()` (jobs de carga, sem custo de consulta).
O `flush()` roda após cada camada e também em caso de falha, para que uma execução que
falha nunca perca a evidência.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

from radar_alfabetizacao.ports import JobStats, Warehouse
from radar_alfabetizacao.quality.engine import RuleResult

log = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(UTC)


class RunRecorder:
    def __init__(
        self,
        warehouse: Warehouse,
        ops_dataset: str,
        run_id: str,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._warehouse = warehouse
        self._ops = ops_dataset
        self.run_id = run_id
        self._clock = clock
        self._runs: list[dict[str, Any]] = []
        self._steps: list[dict[str, Any]] = []
        self._quality: list[dict[str, Any]] = []
        self._command = ""
        self._params = "{}"
        self._started_at: datetime | None = None

    def start(self, command: str, params: Mapping[str, Any] | None = None) -> None:
        self._command = command
        self._params = json.dumps(dict(params or {}), default=str)
        self._started_at = self._clock()
        self._runs.append(self._run_row("running", None))

    def step(
        self,
        name: str,
        stats: JobStats | None = None,
        *,
        status: str = "ok",
        detail: str | None = None,
    ) -> None:
        stats = stats or JobStats()
        self._steps.append(
            {
                "run_id": self.run_id,
                "step": name,
                "status": status,
                "job_id": stats.job_id or None,
                "rows_affected": stats.rows_affected,
                "bytes_processed": stats.bytes_processed,
                "bytes_billed": stats.bytes_billed,
                "duration_seconds": round(stats.duration_seconds, 3),
                "detail": detail,
                "recorded_at": self._clock().isoformat(),
            }
        )

    def quality(self, results: Iterable[RuleResult]) -> None:
        for r in results:
            self._quality.append(
                {
                    "run_id": self.run_id,
                    "layer": r.layer,
                    "rule_id": r.rule_id,
                    "severity": str(r.severity),
                    "passed": r.passed,
                    "observed": r.observed,
                    "expectation": r.expectation,
                    "message": r.message,
                    "checked_at": self._clock().isoformat(),
                }
            )

    def finish(self, status: str, error: str | None = None) -> None:
        self._runs.append(self._run_row(status, error))

    def flush(self) -> None:
        for table, rows in (
            ("runs", self._runs),
            ("steps", self._steps),
            ("quality_results", self._quality),
        ):
            if rows:
                self._warehouse.load_rows(f"{self._ops}.{table}", rows, step=f"ops.{table}")
                rows.clear()

    def safe_flush(self) -> None:
        """Descarrega sem mascarar o erro original quando o próprio registro falha."""
        try:
            self.flush()
        except Exception:
            log.exception("não foi possível gravar o registro da execução")

    def _run_row(self, status: str, error: str | None) -> dict[str, Any]:
        finished = status != "running"
        return {
            "run_id": self.run_id,
            "command": self._command,
            "status": status,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "finished_at": self._clock().isoformat() if finished else None,
            "error": error,
            "params": self._params,
            "recorded_at": self._clock().isoformat(),
        }
