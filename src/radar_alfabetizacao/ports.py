"""Contratos (portas) entre o núcleo do pipeline e a infraestrutura de nuvem.

O núcleo depende só destes protocolos; os adaptadores reais ficam em `adapters/`.
Nos testes, substituímos por implementações em memória.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass(frozen=True)
class JobStats:
    job_id: str = ""
    bytes_processed: int = 0
    bytes_billed: int = 0
    rows_affected: int | None = None
    duration_seconds: float = 0.0
    statement_type: str = ""


@dataclass(frozen=True)
class QueryResult:
    rows: list[dict[str, Any]]
    stats: JobStats


@dataclass(frozen=True)
class TableInfo:
    table: str
    num_rows: int
    num_bytes: int
    modified_at: datetime
    columns: dict[str, str] = field(default_factory=dict)


class Warehouse(Protocol):
    def query(
        self, sql: str, *, step: str, params: Mapping[str, Any] | None = None
    ) -> QueryResult: ...

    def table_info(self, table: str) -> TableInfo: ...

    def dataset_storage(self, datasets: Sequence[str]) -> tuple[int, int]:
        """Bytes lógicos armazenados (ativo, longo prazo) somando todas as tabelas dos datasets."""
        ...

    def load_rows(
        self,
        table: str,
        rows: Sequence[Mapping[str, Any]],
        *,
        step: str,
        schema: Sequence[tuple[str, str]] | None = None,
        ttl_hours: int | None = None,
        truncate: bool = False,
    ) -> JobStats: ...


@dataclass(frozen=True)
class ReceivedMessage:
    message_id: str
    data: bytes
    publish_time: datetime
    ack_id: str
    attributes: Mapping[str, str] = field(default_factory=dict)


class MessageSource(Protocol):
    def pull(self, max_messages: int) -> list[ReceivedMessage]: ...

    def ack(self, ack_ids: Sequence[str]) -> None: ...


class MessagePublisher(Protocol):
    def publish_all(self, messages: Sequence[tuple[bytes, Mapping[str, str]]]) -> int: ...
