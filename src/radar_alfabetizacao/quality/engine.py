"""Motor de regras. Cada regra é um SQL que devolve uma linha com a coluna `observed`.

Regras bloqueantes impedem a publicação da camada seguinte; informativas só são registradas.
O motor executa TODAS as regras da camada antes de decidir, para que a evidência fique completa.
"""

from __future__ import annotations

import math
import operator
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from radar_alfabetizacao.contract import RuleSpec, Severity
from radar_alfabetizacao.ports import JobStats, Warehouse
from radar_alfabetizacao.sqlrender import SqlRenderer

_OPERATORS: dict[str, Callable[[float, float], bool]] = {
    "<=": operator.le,
    ">=": operator.ge,
    "<": operator.lt,
    ">": operator.gt,
}


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    layer: str
    severity: Severity
    passed: bool
    observed: float | None
    expectation: str
    message: str


@dataclass(frozen=True)
class RuleOutcome:
    result: RuleResult
    stats: JobStats | None = None


class QualityGateError(RuntimeError):
    def __init__(self, layer: str, failed: Sequence[RuleResult]) -> None:
        self.layer = layer
        self.failed = list(failed)
        ids = ", ".join(r.rule_id for r in self.failed)
        super().__init__(f"Gate de qualidade '{layer}' falhou: {ids}")


def evaluate(op: str, observed: float | None, value: float) -> bool:
    """Compara o valor observado com a expectativa. Sem observação, a regra falha."""
    if observed is None:
        return False
    if op == "==":
        return math.isclose(observed, value, abs_tol=1e-9)
    return _OPERATORS[op](observed, value)


def build_result(rule: RuleSpec, observed: float | None, note: str = "") -> RuleResult:
    passed = evaluate(rule.op, observed, rule.value)
    expectation = f"{rule.op} {rule.value:g}"
    shown = "sem valor" if observed is None else f"{observed:g}"
    message = f"{rule.description}: observado {shown}, esperado {expectation}"
    return RuleResult(
        rule_id=rule.id,
        layer=rule.layer,
        severity=rule.severity,
        passed=passed,
        observed=observed,
        expectation=expectation,
        message=f"{message}. {note}".strip() if note else message,
    )


class QualityEngine:
    def __init__(
        self, warehouse: Warehouse, renderer: SqlRenderer, rules: Sequence[RuleSpec]
    ) -> None:
        self._warehouse = warehouse
        self._renderer = renderer
        self._rules = list(rules)

    def run_layer(self, layer: str, context: Mapping[str, Any]) -> list[RuleOutcome]:
        outcomes: list[RuleOutcome] = []
        for rule in (r for r in self._rules if r.layer == layer):
            try:
                sql = self._renderer.render_string(rule.sql, **context)
                result = self._warehouse.query(sql, step=f"quality.{rule.id}")
                raw = result.rows[0].get("observed") if result.rows else None
                observed = None if raw is None else float(raw)
                outcomes.append(RuleOutcome(build_result(rule, observed), result.stats))
            except Exception as exc:
                note = f"erro ao executar a regra: {type(exc).__name__}: {exc}"
                failed = build_result(rule, None, note)
                outcomes.append(RuleOutcome(failed))
        return outcomes
