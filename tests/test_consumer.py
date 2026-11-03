import json
from datetime import timedelta

import pytest

from radar_alfabetizacao.domain.eventos import construir_evento
from radar_alfabetizacao.pipeline.consumer import percentile, run_consumer
from radar_alfabetizacao.pipeline.faults import build_fault_messages
from radar_alfabetizacao.ports import ReceivedMessage
from tests.conftest import NOW, FakeSource

LINHA = {
    "ano": 2024,
    "sigla_uf": "CE",
    "rede": "Pública",
    "taxa_alfabetizacao": 78.5,
    "meta_alfabetizacao_2024": 70.0,
    "meta_alfabetizacao_2030": 80.0,
    "percentual_participacao": 97.0,
}


def evento(contract, **mudancas):
    return construir_evento(
        "meta_alfabetizacao_uf",
        {**LINHA, **mudancas},
        contract,
        source_version="v1",
        produced_at=NOW - timedelta(minutes=10),
    )


def msg(i: int, data: bytes, segundos_atras: float = 2.0) -> ReceivedMessage:
    return ReceivedMessage(f"m{i}", data, NOW - timedelta(seconds=segundos_atras), f"ack{i}")


@pytest.mark.parametrize(
    ("valores", "q", "esperado"),
    [
        ([], 0.5, None),
        ([5.0], 0.95, 5.0),
        ([1.0, 2.0, 3.0, 4.0], 0.5, 2.0),
        ([1.0, 2.0, 3.0, 4.0], 0.95, 4.0),
    ],
)
def test_percentile(valores, q, esperado):
    assert percentile(valores, q) == esperado


def test_lote_misto_separa_validos_quarentena_e_duplicados(ctx, warehouse, contract):
    ok = evento(contract)
    outro = evento(contract, sigla_uf="SP", taxa_alfabetizacao=60.0)
    lote = [
        msg(1, ok.to_message()),
        msg(2, ok.to_message()),  # duplicata no lote
        msg(3, outro.to_message()),
        msg(4, b"lixo"),
        msg(5, json.dumps({**ok.model_dump(mode="json"), "taxa_alfabetizacao": 140.0}).encode()),
    ]
    warehouse.responses["stream.ledger_check"] = [{"observed": 0}]
    source = FakeSource([lote])

    totals = run_consumer(ctx, source, max_batches=3)

    assert (totals.pulled, totals.valid, totals.quarantined, totals.merged_new) == (5, 3, 2, 2)
    assert totals.duplicates == 1
    assert len(source.acked) == 5  # tudo é confirmado: inválidas ficam na quarentena
    bruto = warehouse.loaded("stream_events")
    assert [r["valid"] for r in bruto] == [True, True, True, False, False]
    assert "fora de 0 a 100" in bruto[4]["reasons"]
    lote_gravado = warehouse.loaded("stream_batches")[0]
    assert lote_gravado["quarantined"] == 2 and lote_gravado["status"] == "partial"
    assert lote_gravado["latency_p50_seconds"] == pytest.approx(2.0)


def test_ack_acontece_somente_depois_do_commit(ctx, warehouse, contract):
    source = FakeSource([[msg(1, evento(contract).to_message())]])
    source.events = warehouse.events
    warehouse.responses["stream.ledger_check"] = [{"observed": 0}]

    run_consumer(ctx, source)

    eventos = warehouse.events
    assert eventos.index("query:stream.commit") < eventos.index("ack")


def test_falha_no_commit_nao_confirma_as_mensagens(ctx, warehouse, contract):
    source = FakeSource([[msg(1, evento(contract).to_message())]])
    warehouse.responses["stream.ledger_check"] = [{"observed": 0}]
    warehouse.failing_steps = {"stream.commit"}

    with pytest.raises(RuntimeError, match="falha simulada"):
        run_consumer(ctx, source)

    assert source.acked == []  # reentrega garantida
    runs = warehouse.loaded("runs")
    assert runs[-1]["status"] == "failed"


def test_evento_ja_no_ledger_conta_como_duplicado(ctx, warehouse, contract):
    source = FakeSource([[msg(1, evento(contract).to_message())]])
    warehouse.responses["stream.ledger_check"] = [{"observed": 1}]

    totals = run_consumer(ctx, source)

    assert (totals.merged_new, totals.duplicates) == (0, 1)


def test_sem_mensagens_nao_toca_o_gold(ctx, warehouse):
    totals = run_consumer(ctx, FakeSource([]))
    assert totals.pulled == 0
    assert not any(step == "stream.commit" for step, _ in warehouse.queries)


def test_mensagens_de_falha_injetada_nunca_chegam_ao_gold(ctx, warehouse, contract):
    mensagens = build_fault_messages(evento(contract))
    assert all(attrs == {"origem": "simulado"} for _, attrs in mensagens)
    lote = [msg(i, data) for i, (data, _) in enumerate(mensagens)]
    warehouse.responses["stream.ledger_check"] = [{"observed": 0}]

    totals = run_consumer(ctx, FakeSource([lote]))

    assert totals.quarantined == len(mensagens) - 2  # só as duas cópias do evento real são válidas
    assert totals.duplicates == 1  # a duplicata do evento real
