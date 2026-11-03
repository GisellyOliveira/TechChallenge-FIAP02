import pytest

from radar_alfabetizacao.ops.finops import (
    GIB,
    Measurements,
    RunCost,
    collect_measurements,
    load_prices,
    project,
    render_markdown,
)
from tests.conftest import ROOT

MIB = 1024**2


@pytest.fixture
def prices():
    return load_prices(ROOT / "config" / "finops_prices.yaml")


def medidas(**mudancas) -> Measurements:
    base = {
        "run_costs": {
            ("batch", "sem_mudancas"): RunCost(5, 40 * MIB, 20.0),
            ("batch", "completo"): RunCost(2, 600 * MIB, 120.0),
            ("detect", "completo"): RunCost(3, 50 * MIB, 15.0),
            ("detect", "sem_mudancas"): RunCost(3, 10 * MIB, 8.0),
            ("consume", "completo"): RunCost(10, 30 * MIB, 25.0),
            ("consume", "sem_mudancas"): RunCost(10, 0.0, 33.0),
        },
        "bq_ativo_bytes": 2 * GIB,
        "bq_longo_bytes": 0.0,
        "gcs_bytes": 0.3 * GIB,
        "pubsub_bytes": 2_000_000.0,
        "total_bytes_faturados": 2 * GIB,
    }
    return Measurements(**{**base, **mudancas})


def test_projecao_do_desafio_cabe_nas_franquias_gratuitas(prices):
    projecao = project(medidas(), prices)
    assert projecao.total == 0.0
    assert projecao.total_sem_franquia > 0.0
    assert [linha.servico.split(":")[0] for linha in projecao.lines] == [
        "BigQuery", "BigQuery", "Cloud Storage", "Pub/Sub", "Cloud Run Jobs", "Cloud Scheduler",
    ]  # fmt: skip


def test_acima_da_franquia_o_custo_aparece(prices):
    projecao = project(medidas(bq_ativo_bytes=50 * GIB), prices)
    armazenamento = projecao.lines[1]
    assert armazenamento.custo_mensal == pytest.approx((50 - 10) * 0.023)


def test_analise_extrapola_execucoes_medidas_pelo_cronograma(prices):
    projecao = project(medidas(), prices)
    # batch: 29,5 x 40 + 0,5 x 600; detect: 119,5 x 10 + 0,5 x 50; consume: 1439,5 x 0 + 0,5 x 30 (MiB)
    esperado_bytes = (29.5 * 40 + 0.5 * 600 + 119.5 * 10 + 0.5 * 50 + 0.5 * 30) * MIB
    assert f"{esperado_bytes / 1024**4:.6f}" in projecao.lines[0].quantidade


def test_execucao_nao_medida_vira_nota_e_nao_zero_silencioso(prices):
    projecao = project(medidas(run_costs={("batch", "completo"): RunCost(1, MIB, 1.0)}), prices)
    assert any("detect" in n for n in projecao.notes)
    assert any("consume" in n for n in projecao.notes)


def test_preco_nao_verificado_gera_aviso(prices):
    pendentes = {
        **prices,
        "cloud_storage": {**prices["cloud_storage"], "verificado": False},
        "cloud_scheduler": {**prices["cloud_scheduler"], "verificado": False},
    }
    notas = " ".join(project(medidas(), pendentes).notes)
    assert "cloud_storage" in notas and "cloud_scheduler" in notas


def test_precos_verificados_nao_geram_aviso(prices):
    assert all(
        v["verificado"] is True
        for v in prices.values()
        if isinstance(v, dict) and "verificado" in v
    )
    assert "ainda não conferidos" not in " ".join(project(medidas(), prices).notes)


def test_markdown_tem_as_colunas_exigidas_pelo_desafio(prices):
    texto = render_markdown(project(medidas(), prices), 3 * MIB, 30)
    cabecalho = (
        "| Serviço | Unidade | Quantidade medida | Preço unitário | Custo mensal projetado |"
    )
    assert cabecalho in texto
    assert "**Total**" in texto and "pior caso" in texto


def test_coleta_le_medidas_do_warehouse(ctx, warehouse):
    warehouse.responses = {
        "finops.comandos": [
            {"comando": "batch", "variante": "completo", "execucoes": 2,
             "bytes_faturados_medios": 1000.0, "segundos_medios": 12.5},
        ],
        "finops.pubsub": [{"mensagens": 3, "bytes": 99}],
        "finops.total": [{"jobs": 4, "bytes_faturados": 123}],
    }  # fmt: skip
    warehouse.storage = (5, 7)
    medida = collect_measurements(ctx, gcs_bytes=11, days=30)
    assert medida.run_costs[("batch", "completo")] == RunCost(2, 1000.0, 12.5)
    assert (medida.bq_ativo_bytes, medida.bq_longo_bytes, medida.pubsub_bytes) == (5, 7, 99)
    assert medida.total_bytes_faturados == 123 and medida.gcs_bytes == 11


def test_variante_nao_medida_usa_o_caso_mais_caro_e_avisa(prices):
    custos = {
        ("batch", "sem_mudancas"): RunCost(1, 40 * MIB, 20.0),
        ("batch", "completo"): RunCost(1, 600 * MIB, 120.0),
        ("detect", "completo"): RunCost(1, 50 * MIB, 15.0),
        ("consume", "completo"): RunCost(1, 30 * MIB, 25.0),
    }
    projecao = project(medidas(run_costs=custos), prices)
    notas = " ".join(projecao.notes)
    assert "'detect' na variante 'sem_mudancas' ainda não foi medido" in notas
    assert "'consume' na variante 'sem_mudancas' ainda não foi medido" in notas
    # conservador: detect e consume ociosos custam como o caso completo medido (50 e 30 MiB)
    esperado = (29.5 * 40 + 0.5 * 600 + 120 * 50 + 1440 * 30) * MIB
    assert f"{esperado / 1024**4:.6f}" in projecao.lines[0].quantidade
