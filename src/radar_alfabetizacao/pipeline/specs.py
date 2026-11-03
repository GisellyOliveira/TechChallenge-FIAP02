"""Especificação declarativa de como cada tabela da fonte vira tabela Silver."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetaSilver:
    """Tabela de meta (larga, uma coluna por ano) padronizada na Silver."""

    source: str
    target: str
    nivel: str
    id_expr: str
    uf_expr: str
    join_uf: bool
    nivel_alfabetizacao_expr: str


META_SILVER: tuple[MetaSilver, ...] = (
    MetaSilver(
        "meta_alfabetizacao_brasil",
        "meta_brasil",
        "brasil",
        "'BR'",
        "CAST(NULL AS STRING)",
        False,
        "CAST(NULL AS INT64)",
    ),
    MetaSilver(
        "meta_alfabetizacao_uf",
        "meta_uf",
        "uf",
        "b.sigla_uf",
        "b.sigla_uf",
        False,
        "CAST(NULL AS INT64)",
    ),
    MetaSilver(
        "meta_alfabetizacao_municipio",
        "meta_municipio",
        "municipio",
        "b.id_municipio",
        "u.sigla_uf",
        True,
        "b.nivel_alfabetizacao",
    ),
)

# (tabela, deriva a sigla da UF a partir do código IBGE?)
RESULTADO_SILVER: tuple[tuple[str, bool], ...] = (("municipio", True), ("uf", False))
