"""Contrato de dados e regras de qualidade, carregados de `config/`."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

_TYPE_ALIASES = {"INT64": "INTEGER", "FLOAT64": "FLOAT", "BOOL": "BOOLEAN"}
_DDL_TYPES = {"INTEGER": "INT64", "FLOAT": "FLOAT64", "BOOLEAN": "BOOL"}
_META_COLUMN = re.compile(r"^meta_alfabetizacao_(\d{4})$")


class Severity(StrEnum):
    BLOCKING = "blocking"
    INFORMATIVE = "informative"


class AnomalyThresholds(BaseModel):
    min_alunos_avaliados: int
    max_divergencia_pp: float
    queda_brusca_pp: float


class TableSpec(BaseModel):
    keys: list[str]
    columns: dict[str, str]
    has_meta_columns: bool = False
    domains: dict[str, list[str]] = Field(default_factory=dict)


class Contract(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: Mapping[str, str]
    cutoff_saeb: float
    meta_window: tuple[int, int]
    plausible_years: tuple[int, int]
    meta_rede_map: dict[str, str]
    watch_tables: list[str]
    freshness_max_days: int
    anomaly: AnomalyThresholds
    uf_ibge: dict[str, str]
    tables: dict[str, TableSpec]

    @property
    def source_dataset(self) -> str:
        return f"{self.source['project']}.{self.source['dataset']}"

    @property
    def first_meta_year(self) -> int:
        return self.meta_window[0]

    @property
    def final_meta_year(self) -> int:
        return self.meta_window[1]


class RuleSpec(BaseModel):
    id: str
    layer: Literal["bronze", "silver", "gold"]
    severity: Severity
    description: str
    sql: str
    op: Literal["==", "<=", ">=", "<", ">"]
    value: float


def load_contract(path: Path) -> Contract:
    return Contract.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def load_rules(path: Path) -> list[RuleSpec]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    rules = [RuleSpec.model_validate(item) for item in raw["rules"]]
    ids = [r.id for r in rules]
    duplicated = {i for i in ids if ids.count(i) > 1}
    if duplicated:
        raise ValueError(f"ids de regras duplicados: {sorted(duplicated)}")
    return rules


def normalize_type(field_type: str) -> str:
    upper = field_type.upper()
    return _TYPE_ALIASES.get(upper, upper)


def ddl_type(field_type: str) -> str:
    """Nome do tipo aceito em DDL do BigQuery (a API de metadados usa nomes legados)."""
    canonical = normalize_type(field_type)
    return _DDL_TYPES.get(canonical, canonical)


def meta_years(columns: Mapping[str, str]) -> list[int]:
    """Anos com coluna `meta_alfabetizacao_<ano>` na tabela real, em ordem crescente."""
    return sorted(int(m.group(1)) for c in columns if (m := _META_COLUMN.match(c)))


@dataclass(frozen=True)
class SchemaDiff:
    missing: tuple[str, ...] = ()
    type_changed: tuple[tuple[str, str, str], ...] = ()
    extra: tuple[str, ...] = ()

    @property
    def breaking(self) -> bool:
        return bool(self.missing or self.type_changed)


def compare_schema(
    spec: TableSpec, actual: Mapping[str, str], meta_window: tuple[int, int]
) -> SchemaDiff:
    """Compara o schema real com o contrato.

    Ausência ou mudança de tipo é quebra (bloqueante). Colunas novas são informativas;
    colunas `meta_alfabetizacao_<ano>` de anos futuros são esperadas e não contam como extras.
    """
    expected = {c: normalize_type(t) for c, t in spec.columns.items()}
    if spec.has_meta_columns:
        for year in range(meta_window[0], meta_window[1] + 1):
            expected[f"meta_alfabetizacao_{year}"] = "FLOAT"
    real = {c: normalize_type(t) for c, t in actual.items()}

    missing = tuple(sorted(c for c in expected if c not in real))
    changed = tuple(
        (c, expected[c], real[c]) for c in sorted(expected) if c in real and real[c] != expected[c]
    )
    extra = tuple(
        sorted(
            c
            for c in real
            if c not in expected and not (spec.has_meta_columns and _META_COLUMN.match(c))
        )
    )
    return SchemaDiff(missing=missing, type_changed=changed, extra=extra)
