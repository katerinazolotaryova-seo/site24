"""Structured logging setup.

Uses `structlog` when available, falling back to stdlib `logging` configured
to emit single-line JSON so log aggregation still works without the extra
dependency. Call `configure_logging()` once at process start (main.py does
this); everywhere else just do `log = get_logger(__name__)`.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

_CONFIGURED = False

try:
    import structlog

    _HAS_STRUCTLOG = True
except ImportError:  # pragma: no cover - exercised only when dep missing
    _HAS_STRUCTLOG = False


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    lvl = getattr(logging, level.upper(), logging.INFO)

    if _HAS_STRUCTLOG:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer() if json_output else structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(lvl),
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JsonFormatter() if json_output else logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)
        root.setLevel(lvl)

    _CONFIGURED = True


class _KwargsLoggerAdapter:
    """Makes stdlib logging accept structlog-style `log.info("event", k=v)`
    calls, so the rest of the codebase doesn't need to care which backend
    is active.
    """

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _log(self, level: int, event: str, **kwargs: Any) -> None:
        self._logger.log(level, event, extra={"extra_fields": kwargs})

    def debug(self, event: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, event, **kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        self._log(logging.INFO, event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, event, **kwargs)

    def exception(self, event: str, **kwargs: Any) -> None:
        self._logger.exception(event, extra={"extra_fields": kwargs})


def get_logger(name: str):
    if not _CONFIGURED:
        configure_logging()
    if _HAS_STRUCTLOG:
        return structlog.get_logger(name)
    return _KwargsLoggerAdapter(logging.getLogger(name))
