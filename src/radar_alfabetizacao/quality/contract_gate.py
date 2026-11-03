"""Regras da camada de contrato: schema, volume e atualidade da fonte oficial."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from radar_alfabetizacao.contract import Contract, Severity, compare_schema
from radar_alfabetizacao.ports import TableInfo
from radar_alfabetizacao.quality.engine import RuleResult

LAYER = "contract"


def schema_results(
    contract: Contract, infos: Mapping[str, TableInfo], now: datetime
) -> list[RuleResult]:
    results: list[RuleResult] = []
    for table, spec in contract.tables.items():
        info = infos[table]
        diff = compare_schema(spec, info.columns, contract.meta_window)
        breaking = len(diff.missing) + len(diff.type_changed)
        detail = f"ausentes={list(diff.missing)} tipos={list(diff.type_changed)}"
        results.append(
            RuleResult(
                f"contract.{table}.schema",
                LAYER,
                Severity.BLOCKING,
                breaking == 0,
                float(breaking),
                "== 0",
                f"Schema de {table} compatível com o contrato: {detail}",
            )
        )
        results.append(
            RuleResult(
                f"contract.{table}.colunas_novas",
                LAYER,
                Severity.INFORMATIVE,
                not diff.extra,
                float(len(diff.extra)),
                "== 0",
                f"Colunas novas na fonte em {table}: {list(diff.extra)}",
            )
        )
        results.append(
            RuleResult(
                f"contract.{table}.nao_vazia",
                LAYER,
                Severity.BLOCKING,
                info.num_rows > 0,
                float(info.num_rows),
                "> 0",
                f"Tabela {table} com linhas na fonte",
            )
        )
    idade = max((now - i.modified_at).days for i in infos.values())
    results.append(
        RuleResult(
            "contract.fonte.defasagem_dias",
            LAYER,
            Severity.INFORMATIVE,
            idade <= contract.freshness_max_days,
            float(idade),
            f"<= {contract.freshness_max_days}",
            "Dias desde a última modificação da fonte mais antiga",
        )
    )
    return results
