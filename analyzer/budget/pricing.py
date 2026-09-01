"""Loads the pricing config (analyzer/resources/dataforseo_pricing.yaml)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class EndpointPricing:
    base_cost_usd: float
    per_row_usd: float

    def estimate(self, row_count: int) -> float:
        return self.base_cost_usd + self.per_row_usd * max(row_count, 0)


def load_pricing_table(path: Path) -> dict[str, EndpointPricing]:
    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    endpoints = raw.get("endpoints", {})
    return {
        name: EndpointPricing(
            base_cost_usd=float(cfg.get("base_cost_usd", 0.0)),
            per_row_usd=float(cfg.get("per_row_usd", 0.0)),
        )
        for name, cfg in endpoints.items()
    }
