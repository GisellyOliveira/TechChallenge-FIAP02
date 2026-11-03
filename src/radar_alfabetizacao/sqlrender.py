"""Renderização dos templates SQL (Jinja). Falta de variável é erro, nunca texto vazio."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined


def sql_list(items: Iterable[object]) -> str:
    """Formata uma lista de literais SQL de texto: ['a', 'b'] -> 'a', 'b'."""
    return ", ".join("'" + str(i).replace("\\", "\\\\").replace("'", "\\'") + "'" for i in items)


class SqlRenderer:
    def __init__(self, sql_dir: Path) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(sql_dir)),
            undefined=StrictUndefined,
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        self._env.filters["sql_list"] = sql_list

    def render(self, template: str, **context: Any) -> str:
        return self._env.get_template(template).render(**context)

    def render_string(self, source: str, **context: Any) -> str:
        return self._env.from_string(source).render(**context)
