"""Logging setup shared by the CLI and (later) the pipeline stages.

Kept deliberately simple for Phase 0 — structured/JSON logging can be added
later without changing call sites, since everything goes through
`get_logger()` rather than the stdlib `logging` module directly.
"""

from __future__ import annotations

import logging
import os

_CONFIGURED = False


def configure_logging(level: str | None = None) -> None:
    """Idempotently configure root logging. Safe to call multiple times."""

    global _CONFIGURED
    if _CONFIGURED:
        return

    resolved_level = (level or os.environ.get("ANALYZER_LOG_LEVEL") or "INFO").upper()
    logging.basicConfig(
        level=resolved_level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
