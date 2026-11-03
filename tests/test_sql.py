"""Todo SQL do repositório é renderizado e analisado sintaticamente (dialeto BigQuery).

Não substitui a execução na nuvem, mas pega no CI erro de template, variável ausente e SQL malformado.
"""

from __future__ import annotations

import pytest
import sqlglot

from radar_alfabetizacao.pipeline.context import PipelineContext
from radar_alfabetizacao.pipeline.specs import META_SILVER, RESULTADO_SILVER
from tests.conftest import ROOT

VERSIONS = {
    "alunos": "a1",
    "municipio": "m1",
    "uf": "u1",
    "dicionario": "d1",
    "meta_alfabetizacao_brasil": "b1",
    "meta_alfabetizacao_uf": "f1",
    "meta_alfabetizacao_municipio": "p1",
}
BATCH_SOURCES = [
    {"nivel": s.nivel, "table": s.target, "version": "v", "modified": "2026-01-01 00:00:00+00:00"}
    for s in META_SILVER
]
YEARS = list(range(2024, 2031))
DATASETS = [
    "alfabetizacao_bronze",
    "alfabetizacao_silver",
    "alfabetizacao_gold",
    "alfabetizacao_ops",
]

EXTRAS: dict[str, dict[str, object]] = {
    "bronze/ingest_version.sql": {
        "table": "alunos",
        "columns": {"ano": "INT64", "taxa": "FLOAT64"},
    },
    "bronze/export_parquet.sql": {"table": "alunos", "version": "a1"},
    "silver/dicionario.sql": {"versions": VERSIONS},
    "silver/alunos.sql": {"versions": VERSIONS},
    "silver/resultado.sql": {"table": "municipio", "derive_uf": True, "versions": VERSIONS},
    "silver/meta.sql": {"spec": META_SILVER[2], "years": YEARS, "versions": VERSIONS},
    "silver/stream_commit.sql": {
        "staging": "p.d.stg",
        "source_template": "gold/termometro_source_stream.sql",
    },
    "gold/termometro_merge.sql": {
        "source_template": "gold/termometro_source_batch.sql",
        "batch_sources": BATCH_SOURCES,
    },
    "stream/fonte.sql": {"table": "meta_alfabetizacao_uf"},
    "stream/duplicados_no_ledger.sql": {"staging": "p.d.stg"},
}
for _name in ("execucoes", "jobs", "qualidade", "reprovadas", "streaming", "tabelas"):
    EXTRAS[f"ops/evidencia_{_name}.sql"] = {"datasets": DATASETS, "project": "proj"}

NOT_TEMPLATES = {
    "macros.sql",
    "gold/termometro_source_batch.sql",
    "gold/termometro_source_stream.sql",
}


def templates() -> list[str]:
    found = sorted(p.relative_to(ROOT / "sql").as_posix() for p in (ROOT / "sql").rglob("*.sql"))
    return [t for t in found if t not in NOT_TEMPLATES]


def parse(sql: str) -> list[object]:
    return [s for s in sqlglot.parse(sql, read="bigquery") if s is not None]


@pytest.mark.parametrize("template", templates())
def test_template_renderiza_e_tem_sintaxe_valida(ctx: PipelineContext, template: str):
    sql = ctx.renderer.render(template, **ctx.sql_context(**EXTRAS.get(template, {})))
    assert sql.strip()
    assert "{{" not in sql and "{%" not in sql
    assert parse(sql), template


@pytest.mark.parametrize(
    "fonte", ["gold/termometro_source_batch.sql", "gold/termometro_source_stream.sql"]
)
def test_fontes_do_merge_compartilham_as_mesmas_colunas(ctx: PipelineContext, fonte: str):
    sql = ctx.renderer.render(
        "gold/termometro_merge.sql",
        **ctx.sql_context(source_template=fonte, batch_sources=BATCH_SOURCES, staging="p.d.stg"),
    )
    assert "MERGE" in sql and parse(sql)


def test_toda_regra_de_qualidade_renderiza_e_tem_sintaxe_valida(ctx: PipelineContext, rules):
    context = ctx.sql_context(versions=VERSIONS, source_rows=dict.fromkeys(ctx.contract.tables, 10))
    for rule in rules:
        sql = ctx.renderer.render_string(rule.sql, **context)
        assert "observed" in sql, rule.id
        assert parse(sql), rule.id


def test_meta_do_ano_usa_so_colunas_que_existem_no_schema_real(ctx: PipelineContext):
    sql = ctx.renderer.render(
        "silver/meta.sql",
        **ctx.sql_context(spec=META_SILVER[1], years=[2024, 2025], versions=VERSIONS),
    )
    assert "meta_alfabetizacao_2025" in sql
    assert "meta_alfabetizacao_2026" not in sql


def test_resultado_silver_cobre_municipio_e_uf():
    assert {t for t, _ in RESULTADO_SILVER} == {"municipio", "uf"}
