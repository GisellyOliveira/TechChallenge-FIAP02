"""Contexto de execução: reúne configuração, contrato, SQL e serviços de uma execução."""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from radar_alfabetizacao.contract import Contract, RuleSpec
from radar_alfabetizacao.ops.recorder import RunRecorder, utc_now
from radar_alfabetizacao.ports import QueryResult, TableInfo, Warehouse
from radar_alfabetizacao.quality.engine import QualityEngine
from radar_alfabetizacao.quality.gate import QualityGate
from radar_alfabetizacao.settings import Settings
from radar_alfabetizacao.sqlrender import SqlRenderer


def new_run_id(now: datetime | None = None) -> str:
    stamp = (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:6]}"


def source_version(info: TableInfo) -> str:
    """Versão da fonte: hash da última modificação, linhas e bytes (tabelas nativas)."""
    key = f"{int(info.modified_at.timestamp() * 1000)}|{info.num_rows}|{info.num_bytes}"
    return hashlib.sha1(key.encode()).hexdigest()[:12]


@dataclass
class PipelineContext:
    settings: Settings
    contract: Contract
    warehouse: Warehouse
    renderer: SqlRenderer
    recorder: RunRecorder
    gate: QualityGate
    run_id: str
    clock: Callable[[], datetime] = utc_now

    @classmethod
    def build(
        cls,
        settings: Settings,
        contract: Contract,
        rules: list[RuleSpec],
        warehouse: Warehouse,
        run_id: str,
    ) -> PipelineContext:
        renderer = SqlRenderer(settings.sql_dir)
        recorder = RunRecorder(warehouse, settings.ops, run_id)
        gate = QualityGate(QualityEngine(warehouse, renderer, rules), recorder)
        return cls(settings, contract, warehouse, renderer, recorder, gate, run_id)

    def sql_context(self, **extra: Any) -> dict[str, Any]:
        base: dict[str, Any] = {
            "src": self.contract.source_dataset,
            "bronze": self.settings.bronze,
            "silver": self.settings.silver,
            "gold": self.settings.gold,
            "ops": self.settings.ops,
            "region": f"region-{self.settings.location.lower()}",
            "bucket": self.settings.bucket,
            "cutoff": self.contract.cutoff_saeb,
            "meta_window": self.contract.meta_window,
            "meta_rede_map": self.contract.meta_rede_map,
            "uf_ibge": self.contract.uf_ibge,
            "anomaly": self.contract.anomaly,
            "contract": self.contract,
            "tables": list(self.contract.tables),
        }
        return {**base, **extra}

    def run_sql(
        self,
        template: str,
        *,
        step: str,
        params: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> QueryResult:
        """Renderiza o template, executa e registra a etapa (job, bytes, duração)."""
        sql = self.renderer.render(template, **self.sql_context(**extra))
        result = self.warehouse.query(sql, step=step, params=params)
        self.recorder.step(step, result.stats)
        return result

    def ensure_schema(self) -> None:
        self.run_sql("ddl/schema.sql", step="ddl.schema")

    def processed_versions(self, consumer: str) -> dict[str, str]:
        result = self.run_sql(
            "ops/processed_versions.sql",
            step=f"ops.processed_versions.{consumer}",
            params={"consumer": consumer},
        )
        return {row["table_name"]: row["source_version"] for row in result.rows}

    def record_versions(
        self, consumer: str, infos: Mapping[str, TableInfo], versions: Mapping[str, str]
    ) -> None:
        now = self.clock().isoformat()
        rows = [
            {
                "table_name": table,
                "consumer": consumer,
                "source_version": versions[table],
                "source_modified_at": infos[table].modified_at.isoformat(),
                "num_rows": infos[table].num_rows,
                "num_bytes": infos[table].num_bytes,
                "run_id": self.run_id,
                "recorded_at": now,
            }
            for table in versions
        ]
        self.warehouse.load_rows(
            f"{self.settings.ops}.source_versions", rows, step="ops.source_versions"
        )
