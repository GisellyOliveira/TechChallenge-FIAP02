"""Indicador Criança Alfabetizada: status frente à meta e taxa ponderada.

Estas funções são a especificação executável das regras. O SQL de produção
(`sql/macros.sql` e `sql/gold/`) implementa as mesmas regras, e os testes verificam
a equivalência.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

LINHA_DE_BASE = "linha_de_base"
SEM_RESULTADO = "sem_resultado"
SEM_META = "sem_meta"
ATINGIU = "atingiu"
NAO_ATINGIU = "nao_atingiu"

STATUS_VALIDOS = (LINHA_DE_BASE, SEM_RESULTADO, SEM_META, ATINGIU, NAO_ATINGIU)


def status_meta(taxa: float | None, meta: float | None, ano: int, primeiro_ano_meta: int) -> str:
    """Classifica o resultado frente à meta, em cinco estados mutuamente exclusivos.

    Ordem de precedência: linha de base, sem resultado, sem meta, atingiu, não atingiu.
    O empate (taxa == meta) conta como "atingiu". Nulo nunca vira zero.
    """
    if ano < primeiro_ano_meta:
        return LINHA_DE_BASE
    if taxa is None:
        return SEM_RESULTADO
    if meta is None:
        return SEM_META
    return ATINGIU if taxa >= meta else NAO_ATINGIU


@dataclass(frozen=True)
class Aluno:
    proficiencia: float | None
    peso: float | None
    presente: bool
    caderno_preenchido: bool


def taxa_alfabetizacao_ponderada(alunos: Iterable[Aluno], corte: float) -> float | None:
    """Taxa (0 a 100) entre alunos avaliados, ponderada pelo peso amostral.

    Avaliado = presente com caderno preenchido. Devolve None quando não há avaliados
    (nunca zero). Avaliado sem proficiência ou peso é erro de dados.
    """
    total = 0.0
    alfabetizados = 0.0
    for aluno in alunos:
        if not (aluno.presente and aluno.caderno_preenchido):
            continue
        if aluno.proficiencia is None or aluno.peso is None:
            raise ValueError("aluno avaliado sem proficiência ou peso")
        total += aluno.peso
        if aluno.proficiencia >= corte:
            alfabetizados += aluno.peso
    if total <= 0:
        return None
    return 100.0 * alfabetizados / total
