"""discovery_log.jsonl writer -- one JSON object per line, append-only, used
both as an audit trail (Stage 20/21) and as the resume source for
checkpoint/resume.
"""

from __future__ import annotations

from pathlib import Path

from src.models import DiscoveryLogEvent


class DiscoveryLogWriter:
    def __init__(self, path: str | Path, truncate: bool = False):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        mode = "w" if truncate else "a"
        # Open/close immediately just to honor truncate; actual writes are
        # appended one line at a time via `log_event`.
        with self.path.open(mode, encoding="utf-8"):
            pass

    def log_event(self, event: DiscoveryLogEvent) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")

    def log(self, stage: str, event_type: str, entity_type: str | None = None, entity_id: str | None = None, **details) -> None:
        self.log_event(
            DiscoveryLogEvent(
                stage=stage,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
            )
        )
