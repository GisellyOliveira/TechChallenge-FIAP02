"""Verificação estática do Terraform (sintaxe e invariantes de segurança) sem precisar do binário."""

from pathlib import Path

import hcl2
import pytest

INFRA = Path(__file__).resolve().parents[1] / "infra"


def limpar(valor):
    """Versões do python-hcl2 diferem em manter ou não as aspas externas de textos e nomes."""
    if isinstance(valor, str):
        return valor[1:-1] if len(valor) > 1 and valor[0] == valor[-1] == '"' else valor
    if isinstance(valor, list):
        return [limpar(v) for v in valor]
    if isinstance(valor, dict):
        return {limpar(k): limpar(v) for k, v in valor.items()}
    return valor


def carregar() -> dict[str, list[dict]]:
    merged: dict[str, list[dict]] = {}
    for arquivo in sorted(INFRA.glob("*.tf")):
        with arquivo.open(encoding="utf-8") as handle:
            parsed = limpar(hcl2.load(handle))
        for bloco, itens in parsed.items():
            merged.setdefault(bloco, []).extend(itens if isinstance(itens, list) else [itens])
    return merged


@pytest.fixture(scope="module")
def tf():
    return carregar()


def recursos(tf, tipo):
    return [r[tipo] for r in tf["resource"] if tipo in r]


def test_todos_os_arquivos_tem_sintaxe_hcl_valida():
    assert carregar()["resource"]


def test_bucket_e_privado_e_com_acesso_uniforme(tf):
    [grupo] = recursos(tf, "google_storage_bucket")
    bucket = next(iter(grupo.values()))
    assert bucket["public_access_prevention"] == "enforced"
    assert bucket["uniform_bucket_level_access"] is True


def test_datasets_ficam_na_mesma_localizacao_da_fonte(tf):
    variaveis = {nome: corpo for v in tf["variable"] for nome, corpo in v.items()}
    assert variaveis["bq_location"]["default"] == "US"


def test_assinatura_tem_dead_letter(tf):
    sub = next(iter(recursos(tf, "google_pubsub_subscription")[0].values()))
    assert sub["dead_letter_policy"][0]["max_delivery_attempts"] == 5


def test_agendamentos_nascem_pausados(tf):
    variaveis = {nome: corpo for v in tf["variable"] for nome, corpo in v.items()}
    assert variaveis["scheduler_enabled"]["default"] is False
    assert variaveis["create_jobs"]["default"] is False


def test_nenhum_papel_de_dono_ou_editor_amplo(tf):
    papeis = [
        corpo["role"]
        for tipo in tf["resource"]
        for nome, grupo in tipo.items()
        if "iam_member" in nome
        for corpo in grupo.values()
    ]
    assert papeis
    assert not {"roles/owner", "roles/editor"} & set(papeis)


def test_alerta_usa_a_metrica_de_falha(tf):
    [grupo] = recursos(tf, "google_logging_metric")
    metrica = next(iter(grupo.values()))
    assert "run_failed" in metrica["filter"]
