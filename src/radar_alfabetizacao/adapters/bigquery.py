"""Adaptador do BigQuery: executa SQL, mede bytes faturados e carrega linhas."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from google.cloud import bigquery

from radar_alfabetizacao.ports import JobStats, QueryResult, TableInfo

_LABEL_INVALID = re.compile(r"[^a-z0-9_-]")


def _label(value: str) -> str:
    return _LABEL_INVALID.sub("_", value.lower())[:63]


def _query_param(name: str, value: Any) -> bigquery.ScalarQueryParameter:
    if isinstance(value, bool):
        return bigquery.ScalarQueryParameter(name, "BOOL", value)
    if isinstance(value, int):
        return bigquery.ScalarQueryParameter(name, "INT64", value)
    if isinstance(value, float):
        return bigquery.ScalarQueryParameter(name, "FLOAT64", value)
    if isinstance(value, datetime):
        return bigquery.ScalarQueryParameter(name, "TIMESTAMP", value)
    return bigquery.ScalarQueryParameter(name, "STRING", str(value))


class BigQueryGateway:
    """Implementa a porta `Warehouse`. Todo job recebe rótulos para o rastreio de custo."""

    def __init__(self, client: bigquery.Client, *, location: str, run_id: str) -> None:
        self._client = client
        self._location = location
        self._run_id = run_id

    def _labels(self, step: str) -> dict[str, str]:
        return {"app": "radar-alfabetizacao", "run_id": _label(self._run_id), "step": _label(step)}

    @staticmethod
    def _stats(job: Any) -> JobStats:
        duration = (job.ended - job.started).total_seconds() if job.started and job.ended else 0.0
        return JobStats(
            job_id=str(job.job_id),
            bytes_processed=int(getattr(job, "total_bytes_processed", 0) or 0),
            bytes_billed=int(getattr(job, "total_bytes_billed", 0) or 0),
            rows_affected=getattr(job, "num_dml_affected_rows", None),
            duration_seconds=duration,
            statement_type=str(getattr(job, "statement_type", "") or ""),
        )

    def query(self, sql: str, *, step: str, params: Mapping[str, Any] | None = None) -> QueryResult:
        config = bigquery.QueryJobConfig(
            query_parameters=[_query_param(k, v) for k, v in (params or {}).items()],
            labels=self._labels(step),
        )
        job = self._client.query(sql, job_config=config, location=self._location)
        rows = [dict(row.items()) for row in job.result()]
        return QueryResult(rows=rows, stats=self._stats(job))

    def table_info(self, table: str) -> TableInfo:
        t = self._client.get_table(table)
        return TableInfo(
            table=table,
            num_rows=int(t.num_rows or 0),
            num_bytes=int(t.num_bytes or 0),
            modified_at=t.modified or datetime.now(UTC),
            columns={f.name: f.field_type for f in t.schema},
        )

    def dataset_storage(self, datasets: Sequence[str]) -> tuple[int, int]:
        """Soma o armazenamento lógico pela API de tabelas (sem consulta e sem custo)."""
        total = long_term = 0
        for dataset in datasets:
            for item in self._client.list_tables(dataset):
                # A biblioteca expõe `num_bytes`, mas não o campo de longo prazo da API.
                resource = self._client.get_table(item.reference).to_api_repr()
                total += int(resource.get("numBytes") or 0)
                long_term += int(resource.get("numLongTermBytes") or 0)
        return total - long_term, long_term

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
        if not rows:
            return JobStats()
        config = bigquery.LoadJobConfig(
            write_disposition=(
                bigquery.WriteDisposition.WRITE_TRUNCATE
                if truncate
                else bigquery.WriteDisposition.WRITE_APPEND
            ),
            labels=self._labels(step),
        )
        if schema:
            config.schema = [bigquery.SchemaField(name, kind) for name, kind in schema]
        job = self._client.load_table_from_json(
            list(rows), table, job_config=config, location=self._location
        )
        job.result()
        if ttl_hours:
            loaded = self._client.get_table(table)
            loaded.expires = datetime.now(UTC) + timedelta(hours=ttl_hours)
            self._client.update_table(loaded, ["expires"])
        return self._stats(job)
