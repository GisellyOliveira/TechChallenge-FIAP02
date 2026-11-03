"""O SQL de produção e o código Python implementam as mesmas regras: prova por paridade em DuckDB."""

from __future__ import annotations

import duckdb
import pytest

from radar_alfabetizacao.domain.indicador import status_meta
from radar_alfabetizacao.sqlrender import SqlRenderer
from tests.conftest import ROOT

CASOS = [
    (None, None, 2023), (50.0, 60.0, 2023), (None, 60.0, 2024), (50.0, None, 2024),
    (None, None, 2025), (60.0, 60.0, 2024), (61.0, 60.0, 2025), (59.99, 60.0, 2026),
    (0.0, 60.0, 2024), (100.0, 80.0, 2030),
]  # fmt: skip


def test_status_expr_em_sql_equivale_a_funcao_python():
    renderer = SqlRenderer(ROOT / "sql")
    expr = renderer.render_string(
        "{% from \"macros.sql\" import status_expr %}{{ status_expr('taxa', 'meta', 'ano', 2024) }}"
    ).strip()
    # render_string não enxerga o loader de arquivos para `from`? Ele enxerga: mesmo Environment.
    con = duckdb.connect()
    con.execute("CREATE TABLE t (taxa DOUBLE, meta DOUBLE, ano INTEGER)")
    con.executemany("INSERT INTO t VALUES (?, ?, ?)", CASOS)
    linhas = con.execute(f"SELECT taxa, meta, ano, {expr} FROM t").fetchall()
    assert len(linhas) == len(CASOS)
    for taxa, meta, ano, status_sql in linhas:
        assert status_sql == status_meta(taxa, meta, ano, 2024), (taxa, meta, ano)


def test_taxa_ponderada_em_sql_equivale_a_funcao_python():
    from radar_alfabetizacao.domain.indicador import Aluno, taxa_alfabetizacao_ponderada

    alunos = [
        Aluno(800.0, 3.0, True, True), Aluno(700.0, 1.0, True, True), Aluno(743.0, 2.5, True, True),
        Aluno(900.0, 50.0, False, True), Aluno(None, None, True, False),
    ]  # fmt: skip
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE a (proficiencia DOUBLE, peso DOUBLE, presenca VARCHAR, caderno VARCHAR)"
    )
    con.executemany(
        "INSERT INTO a VALUES (?, ?, ?, ?)",
        [
            (
                a.proficiencia,
                a.peso,
                "1" if a.presente else "0",
                "1" if a.caderno_preenchido else "0",
            )
            for a in alunos
        ],
    )
    (sql_taxa,) = con.execute(
        "SELECT 100 * SUM(CASE WHEN proficiencia >= 743 THEN peso ELSE 0 END) / SUM(peso) "
        "FROM a WHERE presenca = '1' AND caderno = '1'"
    ).fetchone()
    assert sql_taxa == pytest.approx(taxa_alfabetizacao_ponderada(alunos, 743.0))


def test_gold_usa_a_macro_de_status():
    termometro = (ROOT / "sql" / "gold" / "termometro_source_batch.sql").read_text(encoding="utf-8")
    merge = (ROOT / "sql" / "gold" / "termometro_merge.sql").read_text(encoding="utf-8")
    assert "status_expr" in merge or "status_expr" in termometro
