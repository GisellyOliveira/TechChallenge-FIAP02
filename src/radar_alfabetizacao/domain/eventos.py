"""Eventos de streaming: construção a partir de linhas oficiais, identidade e validação.

Um evento é uma linha publicada de uma tabela de meta oficial. O `event_id` é o hash do
conteúdo: a mesma linha republicada gera o mesmo id (duplicata); se o valor oficial mudar,
nasce um id novo (nova versão).
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict

from radar_alfabetizacao.contract import Contract
from radar_alfabetizacao.domain.territorio import is_ibge_municipio, uf_do_municipio

EVENT_TYPE = "resultado_meta_publicado"
NIVEL_POR_TABELA = {
    "meta_alfabetizacao_brasil": "brasil",
    "meta_alfabetizacao_uf": "uf",
    "meta_alfabetizacao_municipio": "municipio",
}
ORIGENS = ("oficial", "simulado")
TOLERANCIA_RELOGIO = timedelta(minutes=5)
_METRICAS = ("taxa_alfabetizacao", "meta_ano", "meta_final", "percentual_participacao")
_OBRIGATORIOS = (
    "event_id",
    "event_type",
    "nivel",
    "id_territorio",
    "ano",
    "rede_codigo",
    "origem_dado",
    "source_table",
    "source_version",
    "produced_at",
)


class ContractViolation(ValueError):
    """A fonte trouxe um valor que o contrato de dados não prevê."""


class Evento(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str
    event_type: str
    nivel: str
    id_territorio: str
    sigla_uf: str | None
    ano: int
    rede_codigo: str
    taxa_alfabetizacao: float | None
    meta_ano: float | None
    meta_final: float | None
    percentual_participacao: float | None
    origem_dado: str
    source_table: str
    source_version: str
    produced_at: datetime

    def to_message(self) -> bytes:
        return json.dumps(self.model_dump(mode="json"), ensure_ascii=False).encode("utf-8")


@dataclass(frozen=True)
class ResultadoValidacao:
    evento: Evento | None
    motivos: list[str] = field(default_factory=list)

    @property
    def valido(self) -> bool:
        return self.evento is not None


def _numero(value: Any) -> float | None:
    if value is None:
        return None
    number = float(value)
    return None if math.isnan(number) else number


def identificar(
    source_table: str,
    nivel: str,
    id_territorio: str,
    ano: int,
    rede_codigo: str,
    metricas: Mapping[str, float | None],
) -> str:
    """Hash do conteúdo. Não inclui horário nem origem: identidade é o fato publicado."""
    conteudo = [
        source_table,
        nivel,
        id_territorio,
        ano,
        rede_codigo,
        [metricas.get(m) for m in _METRICAS],
    ]
    return hashlib.sha256(json.dumps(conteudo, separators=(",", ":")).encode()).hexdigest()


def construir_evento(
    tabela: str,
    linha: Mapping[str, Any],
    contract: Contract,
    *,
    source_version: str,
    produced_at: datetime,
    origem: str = "oficial",
) -> Evento:
    """Converte uma linha de tabela de meta oficial em evento normalizado."""
    nivel = NIVEL_POR_TABELA[tabela]
    rede_texto = linha["rede"]
    if rede_texto not in contract.meta_rede_map:
        raise ContractViolation(f"rede sem mapeamento no contrato: {rede_texto!r} em {tabela}")
    ano = int(linha["ano"])
    if nivel == "brasil":
        id_territorio, sigla_uf = "BR", None
    elif nivel == "uf":
        id_territorio = sigla_uf = str(linha["sigla_uf"])
    else:
        id_territorio = str(linha["id_municipio"])
        sigla_uf = uf_do_municipio(id_territorio, contract.uf_ibge)
    metricas = {
        "taxa_alfabetizacao": _numero(linha.get("taxa_alfabetizacao")),
        "meta_ano": _numero(linha.get(f"meta_alfabetizacao_{ano}")),
        "meta_final": _numero(linha.get(f"meta_alfabetizacao_{contract.final_meta_year}")),
        "percentual_participacao": _numero(linha.get("percentual_participacao")),
    }
    rede_codigo = contract.meta_rede_map[rede_texto]
    return Evento(
        event_id=identificar(tabela, nivel, id_territorio, ano, rede_codigo, metricas),
        event_type=EVENT_TYPE,
        nivel=nivel,
        id_territorio=id_territorio,
        sigla_uf=sigla_uf,
        ano=ano,
        rede_codigo=rede_codigo,
        origem_dado=origem,
        source_table=tabela,
        source_version=source_version,
        produced_at=produced_at,
        **metricas,
    )


def _validar_territorio(nivel: str, id_territorio: str, contract: Contract) -> str | None:
    if nivel == "brasil":
        return None if id_territorio == "BR" else "id_territorio deve ser BR no nível brasil"
    if nivel == "uf":
        if id_territorio in contract.uf_ibge.values():
            return None
        return f"sigla de UF desconhecida: {id_territorio}"
    if not is_ibge_municipio(id_territorio):
        return f"código IBGE de município inválido: {id_territorio}"
    if uf_do_municipio(id_territorio, contract.uf_ibge) is None:
        return f"município de UF desconhecida: {id_territorio}"
    return None


def validar_mensagem(data: bytes, contract: Contract, agora: datetime) -> ResultadoValidacao:
    """Valida uma mensagem recebida. Reúne TODOS os motivos de rejeição, não só o primeiro."""
    try:
        bruto = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ResultadoValidacao(None, ["mensagem não é JSON válido"])
    if not isinstance(bruto, dict):
        return ResultadoValidacao(None, ["mensagem deve ser um objeto JSON"])

    motivos: list[str] = [
        f"campo obrigatório ausente: {c}" for c in _OBRIGATORIOS if bruto.get(c) is None
    ]
    if motivos:
        return ResultadoValidacao(None, motivos)

    if bruto["event_type"] != EVENT_TYPE:
        motivos.append(f"event_type desconhecido: {bruto['event_type']}")
    if bruto["nivel"] not in NIVEL_POR_TABELA.values():
        motivos.append(f"nível desconhecido: {bruto['nivel']}")
    else:
        erro = _validar_territorio(bruto["nivel"], str(bruto["id_territorio"]), contract)
        if erro:
            motivos.append(erro)
    if bruto["origem_dado"] not in ORIGENS:
        motivos.append(f"origem_dado desconhecida: {bruto['origem_dado']}")
    if str(bruto["rede_codigo"]) not in set(contract.meta_rede_map.values()):
        motivos.append(f"rede_codigo fora do domínio: {bruto['rede_codigo']}")

    try:
        ano = int(bruto["ano"])
    except (TypeError, ValueError):
        ano = None
        motivos.append("ano não é inteiro")
    if ano is not None and not (contract.plausible_years[0] <= ano <= contract.plausible_years[1]):
        motivos.append(f"ano fora do intervalo plausível: {ano}")

    metricas: dict[str, float | None] = {}
    for nome in _METRICAS:
        try:
            valor = _numero(bruto.get(nome))
        except (TypeError, ValueError):
            motivos.append(f"{nome} não é numérico")
            continue
        if valor is not None and not 0.0 <= valor <= 100.0:
            motivos.append(f"{nome} fora de 0 a 100: {valor}")
        metricas[nome] = valor

    produced_at = None
    try:
        produced_at = datetime.fromisoformat(str(bruto["produced_at"]))
        if produced_at.tzinfo is None:
            motivos.append("produced_at sem fuso horário")
        elif produced_at > agora + TOLERANCIA_RELOGIO:
            motivos.append("produced_at no futuro")
    except ValueError:
        motivos.append("produced_at não é uma data ISO válida")

    if not motivos and ano is not None:
        esperado = identificar(
            str(bruto["source_table"]),
            str(bruto["nivel"]),
            str(bruto["id_territorio"]),
            ano,
            str(bruto["rede_codigo"]),
            metricas,
        )
        if esperado != bruto["event_id"]:
            motivos.append("event_id não corresponde ao conteúdo")

    if motivos or ano is None or produced_at is None:
        return ResultadoValidacao(None, motivos)

    id_territorio = str(bruto["id_territorio"])
    sigla_uf = {
        "brasil": None,
        "uf": id_territorio,
        "municipio": uf_do_municipio(id_territorio, contract.uf_ibge),
    }[str(bruto["nivel"])]
    evento = Evento(
        event_id=str(bruto["event_id"]),
        event_type=str(bruto["event_type"]),
        nivel=str(bruto["nivel"]),
        id_territorio=id_territorio,
        sigla_uf=sigla_uf,
        ano=ano,
        rede_codigo=str(bruto["rede_codigo"]),
        origem_dado=str(bruto["origem_dado"]),
        source_table=str(bruto["source_table"]),
        source_version=str(bruto["source_version"]),
        produced_at=produced_at.astimezone(UTC),
        **metricas,
    )
    return ResultadoValidacao(evento)
