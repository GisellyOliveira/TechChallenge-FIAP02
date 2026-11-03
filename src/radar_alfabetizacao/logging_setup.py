"""Logs estruturados em JSON (um objeto por linha), lidos nativamente pelo Cloud Logging."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

_STANDARD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
}


_RESERVED = {"severity", "message", "logger", "time"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
        }
        extras = {k: v for k, v in record.__dict__.items() if k not in _STANDARD_ATTRS}
        # Campos extras nunca sobrescrevem os que o Cloud Logging interpreta (severity, message...).
        payload.update({k: v for k, v in extras.items() if k not in _RESERVED})
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())


def log_event(
    logger: logging.Logger,
    event: str,
    message: str = "",
    *,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    """Registra um evento nomeado. O campo `event` alimenta a métrica de alerta (run_failed)."""
    logger.log(level, message or event, extra={"event": event, **fields})
