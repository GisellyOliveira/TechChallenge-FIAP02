import pytest

from radar_alfabetizacao.domain.indicador import (
    ATINGIU,
    LINHA_DE_BASE,
    NAO_ATINGIU,
    SEM_META,
    SEM_RESULTADO,
    Aluno,
    status_meta,
    taxa_alfabetizacao_ponderada,
)


@pytest.mark.parametrize(
    ("taxa", "meta", "ano", "esperado"),
    [
        (50.0, 60.0, 2023, LINHA_DE_BASE),
        (None, 60.0, 2023, LINHA_DE_BASE),
        (None, 60.0, 2024, SEM_RESULTADO),
        (50.0, None, 2024, SEM_META),
        (None, None, 2024, SEM_RESULTADO),
        (60.0, 60.0, 2024, ATINGIU),
        (60.1, 60.0, 2024, ATINGIU),
        (59.9, 60.0, 2024, NAO_ATINGIU),
        (0.0, 60.0, 2024, NAO_ATINGIU),
    ],
)
def test_status_meta(taxa, meta, ano, esperado):
    assert status_meta(taxa, meta, ano, 2024) == esperado


def test_taxa_ponderada_usa_peso_e_ignora_nao_avaliados():
    alunos = [
        Aluno(800.0, 3.0, True, True),  # alfabetizado, peso 3
        Aluno(700.0, 1.0, True, True),  # não alfabetizado, peso 1
        Aluno(900.0, 50.0, False, True),  # ausente: ignorado
        Aluno(None, None, True, False),  # caderno em branco: ignorado
    ]
    assert taxa_alfabetizacao_ponderada(alunos, 743.0) == pytest.approx(75.0)


def test_corte_e_inclusivo():
    assert taxa_alfabetizacao_ponderada([Aluno(743.0, 2.0, True, True)], 743.0) == 100.0


def test_sem_avaliados_devolve_none_e_nunca_zero():
    assert taxa_alfabetizacao_ponderada([Aluno(None, None, False, False)], 743.0) is None
    assert taxa_alfabetizacao_ponderada([], 743.0) is None


def test_avaliado_sem_proficiencia_e_erro_de_dados():
    with pytest.raises(ValueError, match="sem proficiência"):
        taxa_alfabetizacao_ponderada([Aluno(None, 1.0, True, True)], 743.0)
