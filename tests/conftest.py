"""Fixtures compartilhadas: contrato real, contexto de pipeline e dublês em memória."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from radar_alfabetizacao.contract import Contract, RuleSpec, load_contract, load_rules
from radar_alfabetizacao.pipeline.context import PipelineContext
from radar_alfabetizacao.ports import JobStats, QueryResult, ReceivedMessage, TableInfo
from radar_alfabetizacao.settings import Settings

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


@dataclass
class FakeWarehouse:
    """Warehouse em memória: respostas por prefixo de `step` e registro de tudo que foi chamado."""

    infos: dict[str, TableInfo] = field(default_factory=dict)
    responses: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    failing_steps: set[str] = field(default_factory=set)
    storage: tuple[int, int] = (0, 0)
    queries: list[tuple[str, str]] = field(default_factory=list)
    loads: list[tuple[str, list[dict[str, Any]]]] = field(default_factory=list)
    events: list[str] = field(default_factory=list)

    def query(self, sql: str, *, step: str, params: Mapping[str, Any] | None = None) -> QueryResult:
        self.queries.append((step, sql))
        self.events.append(f"query:{step}")
        if any(step.startswith(prefix) for prefix in self.failing_steps):
            raise RuntimeError(f"falha simulada em {step}")
        rows: list[dict[str, Any]] = []
        for prefix, value in sorted(self.responses.items(), key=lambda kv: -len(kv[0])):
            if step.startswith(prefix):
                rows = value
                break
        return QueryResult(
            rows, JobStats(job_id=f"job-{len(self.queries)}", bytes_billed=10_485_760)
        )

    def table_info(self, table: str) -> TableInfo:
        return self.infos[table.split(".")[-1]]

    def dataset_storage(self, datasets: Sequence[str]) -> tuple[int, int]:
        return self.storage

    def load_rows(
        self,
        table: str,
        rows: Sequence[Mapping[str, Any]],
        *,
        step: str,
        schema: Sequence[tuple[str, str]] | None = None,
        ttl_hours: int | None = None,
        truncate: bool = False,
    ) -> JobStats:
        self.events.append(f"load:{step}")
        self.loads.append((table, [dict(r) for r in rows]))
        return JobStats(job_id="load")

    def loaded(self, suffix: str) -> list[dict[str, Any]]:
        return [row for table, rows in self.loads if table.endswith(suffix) for row in rows]


@dataclass
class FakeSource:
    batches: list[list[ReceivedMessage]]
    acked: list[str] = field(default_factory=list)
    events: list[str] | None = None

    def pull(self, max_messages: int) -> list[ReceivedMessage]:
        return self.batches.pop(0) if self.batches else []

    def ack(self, ack_ids: Sequence[str]) -> None:
        self.acked.extend(ack_ids)
        if self.events is not None:
            self.events.append("ack")


@dataclass
class FakePublisher:
    published: list[tuple[bytes, Mapping[str, str]]] = field(default_factory=list)

    def publish_all(self, messages: Sequence[tuple[bytes, Mapping[str, str]]]) -> int:
        self.published.extend(messages)
        return len(messages)


def make_info(
    table: str, columns: Mapping[str, str], *, rows: int = 10, days_old: int = 10
) -> TableInfo:
    return TableInfo(table, rows, rows * 100, NOW - timedelta(days=days_old), dict(columns))


@pytest.fixture(scope="session")
def contract() -> Contract:
    return load_contract(ROOT / "config" / "sources.yaml")


@pytest.fixture(scope="session")
def rules() -> list[RuleSpec]:
    return load_rules(ROOT / "config" / "rules.yaml")


@pytest.fixture
def settings() -> Settings:
    return Settings(  # type: ignore[call-arg]
        _env_file=None,
        project_id="proj",
        bucket="bkt",
        config_dir=ROOT / "config",
        sql_dir=ROOT / "sql",
    )


@pytest.fixture
def warehouse() -> FakeWarehouse:
    return FakeWarehouse()


@pytest.fixture
def ctx(
    settings: Settings, contract: Contract, rules: list[RuleSpec], warehouse: FakeWarehouse
) -> PipelineContext:
    context = PipelineContext.build(settings, contract, rules, warehouse, "run-test")
    context.clock = lambda: NOW
    return context


def source_infos(contract: Contract, *, days_old: int = 10) -> dict[str, TableInfo]:
    """Infos de fonte conformes ao contrato (inclui as colunas de meta de 2024 a 2030)."""
    infos: dict[str, TableInfo] = {}
    for name, spec in contract.tables.items():
        columns = dict(spec.columns)
        if spec.has_meta_columns:
            for year in range(contract.first_meta_year, contract.final_meta_year + 1):
                columns[f"meta_alfabetizacao_{year}"] = "FLOAT"
        infos[name] = make_info(name, columns, days_old=days_old)
    return infos
