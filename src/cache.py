"""Lightweight on-disk request cache.

No extra dependency (avoids diskcache) -- just a sharded JSON-file cache
keyed by sha256(url or key). Good enough for a crawler/search-provider that
needs to avoid re-fetching the same URL across runs and support
checkpoint/resume. Not meant for high-throughput key/value use.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional


class DiskCache:
    def __init__(self, cache_dir: str | Path, ttl_hours: float = 168.0):
        self.dir = Path(cache_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_hours * 3600

    def _path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        shard = digest[:2]
        shard_dir = self.dir / shard
        shard_dir.mkdir(parents=True, exist_ok=True)
        return shard_dir / f"{digest}.json"

    def get(self, key: str) -> Optional[Any]:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as f:
                envelope = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
        if time.time() - envelope.get("_cached_at", 0) > self.ttl_seconds:
            return None
        return envelope.get("value")

    def set(self, key: str, value: Any) -> None:
        path = self._path(key)
        envelope = {"_cached_at": time.time(), "key": key, "value": value}
        with path.open("w", encoding="utf-8") as f:
            json.dump(envelope, f, default=str)

    def get_or_set(self, key: str, producer):
        cached = self.get(key)
        if cached is not None:
            return cached, True
        value = producer()
        self.set(key, value)
        return value, False
