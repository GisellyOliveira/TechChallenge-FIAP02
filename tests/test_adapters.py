"""Adaptadores de nuvem com clientes simulados: garantem rótulos, parâmetros e semântica de ack."""

import json
import logging
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from google.api_core import exceptions as gax

from radar_alfabetizacao.adapters import bigquery as bq_adapter
from radar_alfabetizacao.adapters.bigquery import BigQueryGateway, _label, _query_param
from radar_alfabetizacao.adapters.pubsub import PubSubPublisher, PubSubPuller
from radar_alfabetizacao.adapters.storage import bucket_size_bytes
from radar_alfabetizacao.logging_setup import JsonFormatter, log_event

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def fake_job(**extra):
    base = {
        "job_id": "job-123",
        "started": T0,
        "ended": T0 + timedelta(seconds=4),
        "total_bytes_processed": 100,
        "total_bytes_billed": 10_485_760,
        "num_dml_affected_rows": 7,
        "statement_type": "MERGE",
    }
    job = MagicMock()
    for key, value in {**base, **extra}.items():
        setattr(job, key, value)
    return job


def test_rotulos_sao_validos_para_o_bigquery():
    assert _label("quality.silver.alunos/Regra X") == "quality_silver_alunos_regra_x"
    assert len(_label("a" * 200)) == 63


@pytest.mark.parametrize(
    ("valor", "tipo"),
    [(True, "BOOL"), (3, "INT64"), (1.5, "FLOAT64"), (T0, "TIMESTAMP"), ("x", "STRING")],
)
def test_tipos_de_parametro(valor, tipo):
    assert _query_param("p", valor).type_ == tipo


def test_query_envia_rotulos_parametros_e_devolve_estatisticas():
    client = MagicMock()
    job = fake_job()
    job.result.return_value = [SimpleNamespace(items=lambda: [("observed", 1)])]
    client.query.return_value = job

    result = BigQueryGateway(client, location="US", run_id="20261101T120000Z-ab12cd").query(
        "SELECT 1", step="gold.termometro", params={"run_id": "r1"}
    )

    config = client.query.call_args.kwargs["job_config"]
    assert config.labels == {
        "app": "radar-alfabetizacao",
        "run_id": "20261101t120000z-ab12cd",
        "step": "gold_termometro",
    }
    assert config.query_parameters[0].name == "run_id"
    assert client.query.call_args.kwargs["location"] == "US"
    assert result.rows == [{"observed": 1}]
    assert (result.stats.job_id, result.stats.bytes_billed, result.stats.duration_seconds) == (
        "job-123",
        10_485_760,
        4.0,
    )
    assert result.stats.rows_affected == 7


def test_table_info_devolve_colunas_e_data_de_modificacao():
    client = MagicMock()
    client.get_table.return_value = SimpleNamespace(
        num_rows=5,
        num_bytes=50,
        modified=T0,
        schema=[SimpleNamespace(name="ano", field_type="INTEGER")],
    )
    info = BigQueryGateway(client, location="US", run_id="r").table_info("p.d.t")
    assert (info.num_rows, info.modified_at, info.columns) == (5, T0, {"ano": "INTEGER"})


def test_load_rows_vazio_nao_cria_job():
    client = MagicMock()
    BigQueryGateway(client, location="US", run_id="r").load_rows("p.d.t", [], step="s")
    client.load_table_from_json.assert_not_called()


def test_load_rows_com_schema_truncate_e_expiracao():
    client = MagicMock()
    client.load_table_from_json.return_value = fake_job()
    client.get_table.return_value = SimpleNamespace(expires=None)

    BigQueryGateway(client, location="US", run_id="r").load_rows(
        "p.d.stg",
        [{"a": 1}],
        step="stream.staging",
        schema=[("a", "INT64")],
        ttl_hours=24,
        truncate=True,
    )

    config = client.load_table_from_json.call_args.kwargs["job_config"]
    assert config.write_disposition == bq_adapter.bigquery.WriteDisposition.WRITE_TRUNCATE
    assert [f.name for f in config.schema] == ["a"]
    client.update_table.assert_called_once()
    assert client.update_table.call_args.args[1] == ["expires"]


def test_publisher_publica_dados_e_atributos():
    with patch("radar_alfabetizacao.adapters.pubsub.pubsub_v1.PublisherClient") as cls:
        client = cls.return_value
        client.topic_path.return_value = "projects/p/topics/t"
        client.publish.return_value.result.return_value = "id"
        total = PubSubPublisher("p", "t").publish_all([(b"x", {"origem": "oficial"})])
    client.publish.assert_called_once_with("projects/p/topics/t", b"x", origem="oficial")
    assert total == 1


def test_puller_converte_mensagens_e_trata_timeout():
    with patch("radar_alfabetizacao.adapters.pubsub.pubsub_v1.SubscriberClient") as cls:
        client = cls.return_value
        client.subscription_path.return_value = "projects/p/subscriptions/s"
        item = SimpleNamespace(
            ack_id="ack-1",
            message=SimpleNamespace(
                message_id="m1", data=b"{}", publish_time=T0, attributes={"origem": "simulado"}
            ),
        )
        client.pull.return_value = SimpleNamespace(received_messages=[item])
        puller = PubSubPuller("p", "s")
        [mensagem] = puller.pull(10)
        assert (mensagem.message_id, mensagem.ack_id, mensagem.attributes) == (
            "m1",
            "ack-1",
            {"origem": "simulado"},
        )
        client.pull.side_effect = gax.DeadlineExceeded("sem mensagens")
        assert puller.pull(10) == []


def test_ack_em_blocos_de_mil():
    with patch("radar_alfabetizacao.adapters.pubsub.pubsub_v1.SubscriberClient") as cls:
        client = cls.return_value
        PubSubPuller("p", "s").ack([str(i) for i in range(2500)])
    assert [len(c.kwargs["request"]["ack_ids"]) for c in client.acknowledge.call_args_list] == [
        1000,
        1000,
        500,
    ]


def test_tamanho_do_bucket_soma_os_objetos():
    with patch("radar_alfabetizacao.adapters.storage.storage.Client") as cls:
        cls.return_value.list_blobs.return_value = [
            SimpleNamespace(size=10),
            SimpleNamespace(size=None),
        ]
        assert bucket_size_bytes("p", "b") == 10


def test_log_json_traz_campos_extras_para_o_cloud_logging():
    logger = logging.getLogger("teste.log")
    record = logger.makeRecord("teste.log", logging.ERROR, "f", 1, "falhou", (), None)
    record.event = "run_failed"
    payload = json.loads(JsonFormatter().format(record))
    assert payload["severity"] == "ERROR"
    assert payload["event"] == "run_failed"
    assert payload["message"] == "falhou"


def test_log_event_inclui_o_nome_do_evento(caplog):
    with caplog.at_level(logging.INFO):
        log_event(logging.getLogger("teste.evento"), "run_succeeded", "ok", run_id="r1")
    assert caplog.records[0].event == "run_succeeded"
    assert caplog.records[0].run_id == "r1"


def test_campo_extra_nao_sobrescreve_a_severidade_do_log():
    logger = logging.getLogger("teste.reservado")
    record = logger.makeRecord("teste.reservado", logging.WARNING, "f", 1, "m", (), None)
    record.severity = "blocking"
    record.rule_severity = "blocking"
    payload = json.loads(JsonFormatter().format(record))
    assert payload["severity"] == "WARNING"
    assert payload["rule_severity"] == "blocking"


def _tabela(num_bytes=None, long_term=None):
    """Tabela real da biblioteca (não um dublê): garante que o código usa só atributos existentes."""
    resource = {"tableReference": {"projectId": "p", "datasetId": "d", "tableId": "t"}}
    if num_bytes is not None:
        resource["numBytes"] = str(num_bytes)
        resource["numLongTermBytes"] = str(long_term)
    return bq_adapter.bigquery.Table.from_api_repr(resource)


def test_armazenamento_soma_tabelas_e_separa_longo_prazo():
    client = MagicMock()
    client.list_tables.side_effect = lambda ds: [SimpleNamespace(reference=f"{ds}.t1")]
    client.get_table.return_value = _tabela(1000, 300)
    ativo, longo = BigQueryGateway(client, location="US", run_id="r").dataset_storage(
        ["p.a", "p.b"]
    )
    assert (ativo, longo) == (1400, 600)


def test_armazenamento_ignora_views_sem_tamanho():
    client = MagicMock()
    client.list_tables.return_value = [SimpleNamespace(reference="p.d.v")]
    client.get_table.return_value = _tabela()
    assert BigQueryGateway(client, location="US", run_id="r").dataset_storage(["p.d"]) == (0, 0)
