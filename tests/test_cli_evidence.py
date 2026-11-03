import pytest

from radar_alfabetizacao.cli import build_parser, main
from radar_alfabetizacao.ops.evidence import build_report, rows_to_markdown


def test_parser_aceita_todos_os_comandos():
    parser = build_parser()
    for argv in (
        ["init"], ["batch"], ["batch", "--force"], ["batch", "--demo-gate-failure"], ["detect"],
        ["consume", "--max-batches", "3"], ["inject-faults"], ["finops", "--days", "7"], ["evidence"],
    ):  # fmt: skip
        assert parser.parse_args(argv).command == argv[0]


def test_comando_desconhecido_e_rejeitado():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["apagar-tudo"])


def test_sem_configuracao_obrigatoria_sai_com_codigo_2(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("RADAR_PROJECT_ID", raising=False)
    monkeypatch.delenv("RADAR_BUCKET", raising=False)
    monkeypatch.chdir(tmp_path)  # sem .env
    assert main(["init"]) == 2
    assert "RADAR_PROJECT_ID" in capsys.readouterr().out


def test_tabela_markdown_escapa_barras_e_trata_vazio():
    assert rows_to_markdown([]) == "_Sem registros._"
    texto = rows_to_markdown([{"a": "x|y", "b": None, "c": 1.23456789}])
    assert "x\\|y" in texto and "1.235" in texto


def test_relatorio_de_evidencias_tem_todas_as_secoes(ctx, warehouse):
    warehouse.responses = {"evidence.": [{"coluna": "valor"}]}
    texto = build_report(ctx)
    for titulo in (
        "Execuções recentes",
        "Jobs do BigQuery",
        "Regras reprovadas",
        "Lotes de streaming",
        "Linhas por tabela",
    ):
        assert titulo in texto


@pytest.fixture
def cli_env(monkeypatch, ctx):
    monkeypatch.setenv("RADAR_PROJECT_ID", "proj")
    monkeypatch.setenv("RADAR_BUCKET", "bkt")
    monkeypatch.setattr("radar_alfabetizacao.cli._context", lambda settings: ctx)
    return ctx


def test_cli_init_cria_o_esquema(cli_env, warehouse, capsys):
    assert main(["init"]) == 0
    assert any(step == "ddl.schema" for step, _ in warehouse.queries)
    assert "Esquema operacional pronto" in capsys.readouterr().out


def test_cli_batch_com_demo_de_falha_devolve_codigo_1(cli_env, warehouse, contract, rules):
    from tests.test_pipelines import preparar

    preparar(warehouse, contract, rules)
    assert main(["batch", "--demo-gate-failure"]) == 1


def test_cli_batch_sem_mudancas_devolve_zero(cli_env, warehouse, contract, rules, capsys):
    from tests.test_pipelines import preparar

    preparar(warehouse, contract, rules, processed=True)
    assert main(["batch"]) == 0
    assert "skipped_no_changes" in capsys.readouterr().out


def test_cli_evidence_grava_o_arquivo(cli_env, warehouse, tmp_path):
    destino = tmp_path / "docs" / "evidencias.md"
    assert main(["evidence", "--output", str(destino)]) == 0
    assert destino.read_text(encoding="utf-8").startswith("# Evidências de execução na nuvem")


def test_cli_finops_grava_a_tabela_exigida(cli_env, warehouse, monkeypatch, tmp_path):
    warehouse.responses = {
        "finops.pubsub": [{"mensagens": 0, "bytes": 0}],
        "finops.total": [{"jobs": 1, "bytes_faturados": 10}],
    }
    monkeypatch.setattr("radar_alfabetizacao.adapters.storage.bucket_size_bytes", lambda p, b: 1024)
    destino = tmp_path / "finops.md"
    assert main(["finops", "--output", str(destino)]) == 0
    assert "| Serviço | Unidade |" in destino.read_text(encoding="utf-8")


def test_cli_inject_faults_publica_somente_mensagens_simuladas(
    cli_env, warehouse, contract, monkeypatch, capsys
):
    from tests.conftest import FakePublisher, source_infos

    warehouse.infos = source_infos(contract)
    warehouse.responses["faults.read"] = [
        {
            "ano": 2025,
            "rede": "Pública",
            "taxa_alfabetizacao": 59.0,
            "meta_alfabetizacao_2025": 56.0,
            "meta_alfabetizacao_2030": 80.0,
            "percentual_participacao": 98.0,
        }
    ]
    publicador = FakePublisher()
    monkeypatch.setattr(
        "radar_alfabetizacao.adapters.pubsub.PubSubPublisher", lambda project, topic: publicador
    )
    assert main(["inject-faults"]) == 0
    assert publicador.published
    assert all(attrs == {"origem": "simulado"} for _, attrs in publicador.published)


def test_cli_finops_atualiza_o_bloco_do_readme(cli_env, warehouse, monkeypatch, tmp_path):
    warehouse.responses = {
        "finops.pubsub": [{"mensagens": 0, "bytes": 0}],
        "finops.total": [{"jobs": 1, "bytes_faturados": 10}],
    }
    monkeypatch.setattr("radar_alfabetizacao.adapters.storage.bucket_size_bytes", lambda p, b: 1024)
    readme = tmp_path / "README.md"
    readme.write_text(
        "antes\n<!-- FINOPS:START -->\nvelho\n<!-- FINOPS:END -->\ndepois\n", encoding="utf-8"
    )
    assert main(["finops", "--output", str(tmp_path / "f.md"), "--readme", str(readme)]) == 0
    texto = readme.read_text(encoding="utf-8")
    assert "velho" not in texto
    assert "| Serviço | Unidade |" in texto
    assert texto.startswith("antes\n") and texto.endswith("depois\n")
