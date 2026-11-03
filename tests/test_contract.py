from pathlib import Path

import pytest
import yaml

from radar_alfabetizacao.contract import compare_schema, load_rules, meta_years, normalize_type
from tests.conftest import ROOT, source_infos


def test_normaliza_tipos_equivalentes():
    assert normalize_type("int64") == "INTEGER"
    assert normalize_type("FLOAT64") == "FLOAT"
    assert normalize_type("STRING") == "STRING"


def test_meta_years_descobre_anos_do_schema_real():
    cols = {
        "ano": "INTEGER",
        "meta_alfabetizacao_2025": "FLOAT",
        "meta_alfabetizacao_2024": "FLOAT",
    }
    assert meta_years(cols) == [2024, 2025]


def test_schema_conforme_nao_tem_diferencas(contract):
    for name, info in source_infos(contract).items():
        diff = compare_schema(contract.tables[name], info.columns, contract.meta_window)
        assert not diff.breaking and not diff.extra, name


def test_coluna_ausente_e_mudanca_de_tipo_quebram(contract):
    info = source_infos(contract)["alunos"]
    columns = dict(info.columns)
    del columns["proficiencia"]
    columns["peso_aluno"] = "STRING"
    diff = compare_schema(contract.tables["alunos"], columns, contract.meta_window)
    assert diff.breaking
    assert diff.missing == ("proficiencia",)
    assert diff.type_changed[0][0] == "peso_aluno"


def test_coluna_nova_e_informativa_e_meta_de_ano_futuro_e_esperada(contract):
    info = source_infos(contract)["meta_alfabetizacao_uf"]
    columns = {**info.columns, "coluna_nova": "STRING", "meta_alfabetizacao_2031": "FLOAT"}
    diff = compare_schema(contract.tables["meta_alfabetizacao_uf"], columns, contract.meta_window)
    assert not diff.breaking
    assert diff.extra == ("coluna_nova",)


def test_regras_tem_ids_unicos_e_cobrem_as_tres_camadas(rules):
    assert {r.layer for r in rules} == {"bronze", "silver", "gold"}
    assert len({r.id for r in rules}) == len(rules)


def test_id_de_regra_duplicado_e_rejeitado(tmp_path: Path):
    raw = yaml.safe_load((ROOT / "config" / "rules.yaml").read_text(encoding="utf-8"))
    raw["rules"].append(raw["rules"][0])
    path = tmp_path / "rules.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicados"):
        load_rules(path)


def test_contrato_tem_corte_e_meta_final_do_desafio(contract):
    assert contract.cutoff_saeb == 743.0
    assert contract.final_meta_year == 2030
