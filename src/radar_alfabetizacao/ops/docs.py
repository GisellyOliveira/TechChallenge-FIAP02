"""Atualiza blocos gerados dentro de documentos escritos à mão (entre marcadores HTML)."""

from __future__ import annotations

import re


def replace_block(text: str, name: str, content: str) -> str:
    """Troca o conteúdo entre os marcadores START/END do bloco `name`; erro se faltarem."""
    start, end = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise ValueError(f"marcadores {start} ... {end} não encontrados")
    replacement = f"{start}\n{content.strip()}\n{end}"
    return pattern.sub(lambda _: replacement, text, count=1)
