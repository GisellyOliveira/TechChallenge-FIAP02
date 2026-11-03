import json
from datetime import timedelta

import pytest

from radar_alfabetizacao.domain.eventos import ContractViolation, construir_evento, validar_mensagem
from tests.conftest import NOW

LINHA_UF = {
    "ano": 2024,
    "sigla_uf": "CE",
    "rede": "Pública",
    "taxa_alfabetizacao": 78.5,
    "meta_alfabetizacao_2024": 70.0,
    "meta_alfabetizacao_2030": 80.0,
    "percentual_participacao": 97.0,
}
LINHA_MUNICIPIO = {**LINHA_UF, "id_municipio": "2305506", "rede": "Municipal"}


def evento_uf(contract, **overrides):
    return construir_evento(
        "meta_alfabetizacao_uf",
        {**LINHA_UF, **overrides},
        contract,
        source_version="v1",
        produced_at=NOW - timedelta(hours=1),
    )


def test_constroi_evento_de_uf(contract):
    evento = evento_uf(contract)
    assert (evento.nivel, evento.id_territorio, evento.sigla_uf) == ("uf", "CE", "CE")
    assert evento.rede_codigo == "5"
    assert (evento.meta_ano, evento.meta_final) == (70.0, 80.0)


def test_constroi_evento_de_municipio_deriva_uf_do_codigo_ibge(contract):
    evento = construir_evento(
        "meta_alfabetizacao_municipio",
        LINHA_MUNICIPIO,
        contract,
        source_version="v1",
        produced_at=NOW,
    )
    assert (evento.id_territorio, evento.sigla_uf, evento.rede_codigo) == ("2305506", "CE", "3")


def test_rede_sem_mapeamento_viola_o_contrato(contract):
    with pytest.raises(ContractViolation, match="rede sem mapeamento"):
        evento_uf(contract, rede="Rede Nova")


def test_mesmo_conteudo_gera_mesmo_id_e_valor_novo_gera_id_novo(contract):
    assert evento_uf(contract).event_id == evento_uf(contract).event_id
    assert evento_uf(contract).event_id != evento_uf(contract, taxa_alfabetizacao=79.0).event_id


def test_mensagem_valida_faz_ida_e_volta(contract):
    original = evento_uf(contract)
    resultado = validar_mensagem(original.to_message(), contract, NOW)
    assert resultado.valido
    assert resultado.evento == original


def _mutar(contract, **mudancas):
    payload = json.loads(evento_uf(contract).to_message())
    payload.update(mudancas)
    return json.dumps(payload).encode()


@pytest.mark.parametrize(
    ("mudancas", "trecho"),
    [
        ({"taxa_alfabetizacao": 140.0}, "fora de 0 a 100"),
        ({"rede_codigo": "9"}, "rede_codigo fora do domínio"),
        ({"produced_at": "2027-01-01T00:00:00+00:00"}, "no futuro"),
        ({"produced_at": "2026-01-01T00:00:00"}, "sem fuso"),
        ({"id_territorio": "XX"}, "UF desconhecida"),
        ({"origem_dado": "outra"}, "origem_dado desconhecida"),
        ({"ano": 1900}, "fora do intervalo plausível"),
        ({"event_type": "x"}, "event_type desconhecido"),
        ({"nivel": "regiao"}, "nível desconhecido"),
    ],
)
def test_mensagens_invalidas_sao_rejeitadas_com_motivo(contract, mudancas, trecho):
    resultado = validar_mensagem(_mutar(contract, **mudancas), contract, NOW)
    assert not resultado.valido
    assert any(trecho in motivo for motivo in resultado.motivos)


def test_id_adulterado_e_detectado(contract):
    resultado = validar_mensagem(_mutar(contract, taxa_alfabetizacao=10.0), contract, NOW)
    assert resultado.motivos == ["event_id não corresponde ao conteúdo"]


def test_reune_todos_os_motivos(contract):
    data = _mutar(contract, taxa_alfabetizacao=140.0, rede_codigo="9")
    assert len(validar_mensagem(data, contract, NOW).motivos) == 2


def test_campos_obrigatorios_ausentes(contract):
    payload = json.loads(evento_uf(contract).to_message())
    del payload["ano"]
    resultado = validar_mensagem(json.dumps(payload).encode(), contract, NOW)
    assert resultado.motivos == ["campo obrigatório ausente: ano"]


@pytest.mark.parametrize("bruto", [b"isto nao e json", b"[1, 2]", b"\xff\xfe"])
def test_lixo_nao_derruba_o_validador(contract, bruto):
    assert not validar_mensagem(bruto, contract, NOW).valido
