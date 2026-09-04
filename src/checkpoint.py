"""Checkpoint/resume support for the orchestrator.

Each pipeline stage that has completed writes a small marker file plus a
JSON snapshot of the stage's output entity IDs (not the full payloads --
those live in the discovery log / output CSVs). On resume, the orchestrator
skips any stage whose marker is present and reloads state from the discovery
log instead of re-running expensive discovery/crawling/enrichment work.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


class CheckpointStore:
    def __init__(self, checkpoint_dir: str | Path):
        self.dir = Path(checkpoint_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, stage: str) -> Path:
        return self.dir / f"{stage}.json"

    def is_done(self, stage: str) -> bool:
        return self._path(stage).exists()

    def mark_done(self, stage: str, payload: Optional[dict[str, Any]] = None) -> None:
        with self._path(stage).open("w", encoding="utf-8") as f:
            json.dump(payload or {}, f, default=str)

    def load(self, stage: str) -> Optional[dict[str, Any]]:
        path = self._path(stage)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def clear(self, stage: Optional[str] = None) -> None:
        if stage:
            self._path(stage).unlink(missing_ok=True)
            return
        for p in self.dir.glob("*.json"):
            p.unlink(missing_ok=True)
