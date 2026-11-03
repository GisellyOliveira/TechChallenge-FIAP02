import pytest

from radar_alfabetizacao.ops.docs import replace_block


def test_troca_so_o_bloco_marcado():
    texto = "a\n<!-- X:START -->\nvelho\n<!-- X:END -->\nb\n"
    assert replace_block(texto, "X", "novo") == "a\n<!-- X:START -->\nnovo\n<!-- X:END -->\nb\n"


def test_e_idempotente():
    texto = "<!-- X:START -->\n<!-- X:END -->"
    uma = replace_block(texto, "X", "c")
    assert replace_block(uma, "X", "c") == uma


def test_conteudo_com_barra_invertida_nao_e_interpretado():
    assert "\\1" in replace_block("<!-- X:START --><!-- X:END -->", "X", "\\1")


def test_sem_marcador_e_erro():
    with pytest.raises(ValueError, match="não encontrados"):
        replace_block("sem marcadores", "X", "c")
