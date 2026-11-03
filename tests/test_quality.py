import pytest

from radar_alfabetizacao.contract import RuleSpec, Severity
from radar_alfabetizacao.ops.recorder import RunRecorder
from radar_alfabetizacao.quality.contract_gate import schema_results
from radar_alfabetizacao.quality.engine import (
    QualityEngine,
    QualityGateError,
    build_result,
    evaluate,
)
from radar_alfabetizacao.quality.gate import QualityGate
from radar_alfabetizacao.sqlrender import SqlRenderer
from tests.conftest import NOW, ROOT, FakeWarehouse, source_infos


def regra(
    rule_id="r.um", severity=Severity.BLOCKING, op="==", value=0.0, sql="SELECT 0 AS observed"
):
    return RuleSpec(
        id=rule_id, layer="silver", severity=severity, description="d", sql=sql, op=op, value=value
    )


@pytest.mark.parametrize(
    ("op", "observed", "value", "esperado"),
    [
        ("==", 0.0, 0.0, True),
        ("==", 1.0, 0.0, False),
        ("<=", 1.0, 1.0, True),
        (">=", 0.9, 0.9, True),
        ("<", 1.0, 1.0, False),
        (">", 2.0, 1.0, True),
        ("==", None, 0.0, False),
    ],
)
def test_evaluate(op, observed, value, esperado):
    assert evaluate(op, observed, value) is esperado


def test_build_result_descreve_observado_e_esperado():
    result = build_result(regra(op=">=", value=0.9), 0.5)
    assert not result.passed
    assert "observado 0.5" in result.message and result.expectation == ">= 0.9"


def montar_gate(warehouse: FakeWarehouse, regras):
    renderer = SqlRenderer(ROOT / "sql")
    recorder = RunRecorder(warehouse, "p.ops", "run-1", clock=lambda: NOW)
    return QualityGate(QualityEngine(warehouse, renderer, regras), recorder), recorder


def test_engine_executa_todas_as_regras_mesmo_quando_uma_falha():
    wh = FakeWarehouse(
        responses={"quality.r.a": [{"observed": 5}], "quality.r.b": [{"observed": 0}]}
    )
    gate, _ = montar_gate(wh, [regra("r.a"), regra("r.b")])
    with pytest.raises(QualityGateError) as erro:
        gate.run("silver", {})
    assert [r.rule_id for r in erro.value.failed] == ["r.a"]
    assert {q for q, _ in wh.queries} == {"quality.r.a", "quality.r.b"}


def test_evidencia_e_gravada_antes_da_excecao():
    wh = FakeWarehouse(responses={"quality.r.a": [{"observed": 5}]})
    gate, _ = montar_gate(wh, [regra("r.a")])
    with pytest.raises(QualityGateError):
        gate.run("silver", {})
    gravado = wh.loaded("quality_results")
    assert len(gravado) == 1 and gravado[0]["passed"] is False


def test_regra_informativa_reprovada_nao_bloqueia():
    wh = FakeWarehouse(responses={"quality.r.i": [{"observed": 3}]})
    gate, _ = montar_gate(wh, [regra("r.i", Severity.INFORMATIVE)])
    resultados = gate.run("silver", {})
    assert not resultados[0].passed


def test_regra_que_nao_executa_falha_fechada():
    wh = FakeWarehouse(failing_steps={"quality.r.x"})
    gate, _ = montar_gate(wh, [regra("r.x")])
    with pytest.raises(QualityGateError) as erro:
        gate.run("silver", {})
    assert "erro ao executar a regra" in erro.value.failed[0].message


def test_regra_sem_linhas_falha_fechada():
    wh = FakeWarehouse(responses={})
    gate, _ = montar_gate(wh, [regra("r.vazia")])
    with pytest.raises(QualityGateError):
        gate.run("silver", {})


def test_template_da_regra_usa_o_contexto():
    wh = FakeWarehouse(responses={"quality.r.t": [{"observed": 0}]})
    gate, _ = montar_gate(wh, [regra("r.t", sql="SELECT 0 AS observed FROM `{{ silver }}.alunos`")])
    gate.run("silver", {"silver": "p.s"})
    assert "`p.s.alunos`" in wh.queries[0][1]


def test_contrato_conforme_passa_e_defasagem_e_informativa(contract):
    resultados = schema_results(contract, source_infos(contract, days_old=999), NOW)
    assert all(r.passed for r in resultados if r.severity is Severity.BLOCKING)
    defasagem = next(r for r in resultados if r.rule_id == "contract.fonte.defasagem_dias")
    assert not defasagem.passed and defasagem.severity is Severity.INFORMATIVE


def test_contrato_com_coluna_ausente_bloqueia(contract):
    infos = source_infos(contract)
    cols = dict(infos["municipio"].columns)
    del cols["taxa_alfabetizacao"]
    infos["municipio"] = type(infos["municipio"])("municipio", 10, 1000, NOW, cols)
    falhas = [r for r in schema_results(contract, infos, NOW) if not r.passed]
    assert [r.rule_id for r in falhas] == ["contract.municipio.schema"]
