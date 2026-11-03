import pytest

from radar_alfabetizacao.pipeline.batch import SKIPPED, SUCCEEDED, run_batch
from radar_alfabetizacao.pipeline.context import source_version
from radar_alfabetizacao.pipeline.detector import run_detector
from radar_alfabetizacao.quality.engine import QualityGateError
from tests.conftest import FakePublisher, source_infos

BASE = {
    "ano": 2025,
    "rede": "Pública",
    "taxa_alfabetizacao": 59.0,
    "meta_alfabetizacao_2025": 56.0,
    "meta_alfabetizacao_2030": 80.0,
    "percentual_participacao": 98.0,
}
LINHAS_FONTE = {
    "meta_alfabetizacao_brasil": BASE,
    "meta_alfabetizacao_uf": {**BASE, "sigla_uf": "CE"},
    "meta_alfabetizacao_municipio": {**BASE, "id_municipio": "2305506"},
}


def linhas_da_fonte(warehouse):
    for tabela, linha in LINHAS_FONTE.items():
        warehouse.responses[f"detect.read.{tabela}"] = [linha]


def passing_value(rule):
    return {"<": rule.value - 1, ">": rule.value + 1}.get(rule.op, rule.value)


def preparar(warehouse, contract, rules, *, processed=None):
    warehouse.infos = source_infos(contract)
    for rule in rules:
        warehouse.responses[f"quality.{rule.id}"] = [{"observed": passing_value(rule)}]
    versions = {t: source_version(i) for t, i in warehouse.infos.items()}
    if processed:
        warehouse.responses["ops.processed_versions"] = [
            {"table_name": t, "source_version": versions[t]} for t in versions
        ]
    return versions


def test_primeira_execucao_constroi_bronze_silver_gold(ctx, warehouse, contract, rules):
    preparar(warehouse, contract, rules)

    resultado = run_batch(ctx)

    assert resultado.status == SUCCEEDED
    passos = [step for step, _ in warehouse.queries]
    assert passos.index("silver.alunos") < passos.index("gold.termometro")
    assert sum(
        1 for p in passos if p.startswith("bronze.") and not p.startswith("bronze.export")
    ) == len(contract.tables)
    assert {r["layer"] for r in warehouse.loaded("quality_results")} >= {
        "contract",
        "bronze",
        "silver",
        "gold",
    }
    assert len(warehouse.loaded("source_versions")) == len(contract.tables)
    assert warehouse.loaded("runs")[-1]["status"] == "succeeded"


def test_fonte_inalterada_nao_reprocessa(ctx, warehouse, contract, rules):
    preparar(warehouse, contract, rules, processed=True)

    resultado = run_batch(ctx)

    assert resultado.status == SKIPPED and resultado.changed == []
    assert not any(
        step.startswith(("bronze.", "silver.", "gold.")) for step, _ in warehouse.queries
    )


def test_force_reprocessa_mesmo_sem_mudanca(ctx, warehouse, contract, rules):
    preparar(warehouse, contract, rules, processed=True)
    assert run_batch(ctx, force=True).status == SUCCEEDED


def test_gate_silver_reprovado_bloqueia_gold_e_nao_marca_versao(ctx, warehouse, contract, rules):
    preparar(warehouse, contract, rules)

    with pytest.raises(QualityGateError) as erro:
        run_batch(ctx, demo_gate_failure=True)

    assert erro.value.layer == "silver"
    passos = [step for step, _ in warehouse.queries]
    assert not any(p.startswith("gold.") for p in passos)
    assert warehouse.loaded("source_versions") == []  # será refeito na próxima execução
    reprovadas = [r for r in warehouse.loaded("quality_results") if not r["passed"]]
    assert [r["rule_id"] for r in reprovadas] == ["demo.falha_injetada"]
    assert warehouse.loaded("runs")[-1]["status"] == "failed"


def test_falha_de_schema_da_fonte_bloqueia_antes_de_qualquer_escrita(
    ctx, warehouse, contract, rules
):
    preparar(warehouse, contract, rules)
    info = warehouse.infos["alunos"]
    del info.columns["peso_aluno"]

    with pytest.raises(QualityGateError, match="contract"):
        run_batch(ctx)

    assert not any(step.startswith("bronze.") for step, _ in warehouse.queries)


def test_detector_publica_so_eventos_novos(ctx, warehouse, contract):
    warehouse.infos = source_infos(contract)
    linhas_da_fonte(warehouse)
    publisher = FakePublisher()

    resultado = run_detector(ctx, publisher)

    assert resultado.published == len(contract.watch_tables)
    assert set(resultado.tables_changed) == set(contract.watch_tables)
    corpo, atributos = publisher.published[0]
    assert atributos["origem"] == "oficial" and b'"BR"' in corpo
    assert len(warehouse.loaded("source_versions")) == len(contract.watch_tables)


def test_detector_nao_republica_evento_conhecido(ctx, warehouse, contract):
    warehouse.infos = source_infos(contract)
    linhas_da_fonte(warehouse)
    first = FakePublisher()
    run_detector(ctx, first)
    import json

    ids = [{"event_id": json.loads(c)["event_id"]} for c, _ in first.published]
    warehouse.responses["detect.known"] = ids[:1]
    second = FakePublisher()

    # força a releitura: a fonte "mudou", mas o conteúdo de um evento é idêntico
    run_detector(ctx, second, force=True)

    assert len(second.published) == len(first.published) - 1


def test_detector_sem_mudanca_na_fonte_nao_le_nada(ctx, warehouse, contract):
    warehouse.infos = source_infos(contract)
    warehouse.responses["ops.processed_versions"] = [
        {"table_name": t, "source_version": source_version(warehouse.infos[t])}
        for t in contract.watch_tables
    ]
    publisher = FakePublisher()

    resultado = run_detector(ctx, publisher)

    assert resultado.published == 0 and resultado.tables_changed == []
    assert not any(step.startswith("detect.read") for step, _ in warehouse.queries)


def test_versao_da_fonte_muda_quando_o_conteudo_muda(contract):
    info = source_infos(contract)["alunos"]
    outra = type(info)(
        info.table, info.num_rows + 1, info.num_bytes, info.modified_at, info.columns
    )
    assert source_version(info) != source_version(outra)
    assert source_version(info) == source_version(info)
