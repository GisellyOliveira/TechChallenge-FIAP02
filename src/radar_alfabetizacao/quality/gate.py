"""Portão de qualidade: executa a camada, persiste TODO resultado e só então decide."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any

from radar_alfabetizacao.contract import Severity
from radar_alfabetizacao.logging_setup import log_event
from radar_alfabetizacao.ops.recorder import RunRecorder
from radar_alfabetizacao.quality.engine import (
    QualityEngine,
    QualityGateError,
    RuleOutcome,
    RuleResult,
)

log = logging.getLogger(__name__)


class QualityGate:
    def __init__(self, engine: QualityEngine, recorder: RunRecorder) -> None:
        self._engine = engine
        self._recorder = recorder

    def run(
        self,
        layer: str,
        context: Mapping[str, Any],
        *,
        extra: Sequence[RuleResult] = (),
    ) -> list[RuleResult]:
        outcomes = [RuleOutcome(r) for r in extra] + self._engine.run_layer(layer, context)
        results = [o.result for o in outcomes]
        for outcome in outcomes:
            if outcome.stats is not None:
                self._recorder.step(
                    f"quality.{outcome.result.rule_id}",
                    outcome.stats,
                    status="ok" if outcome.result.passed else "failed",
                )
        self._recorder.quality(results)
        self._recorder.flush()  # a evidência é gravada antes de qualquer exceção
        for r in results:
            log_event(
                log,
                "quality_rule",
                r.message,
                level=logging.INFO if r.passed else logging.WARNING,
                run_id=self._recorder.run_id,
                rule_id=r.rule_id,
                rule_severity=str(r.severity),
                passed=r.passed,
                observed=r.observed,
            )
        failed = [r for r in results if r.severity is Severity.BLOCKING and not r.passed]
        if failed:
            raise QualityGateError(layer, failed)
        return results
