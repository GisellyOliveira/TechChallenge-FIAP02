"""Territórios: código IBGE de município e UF."""

from __future__ import annotations

from collections.abc import Mapping


def is_ibge_municipio(value: str) -> bool:
    return len(value) == 7 and value.isdigit()


def uf_do_municipio(id_municipio: str, uf_ibge: Mapping[str, str]) -> str | None:
    """Sigla da UF a partir dos dois primeiros dígitos do código IBGE; None se inválido."""
    if not is_ibge_municipio(id_municipio):
        return None
    return uf_ibge.get(id_municipio[:2])
