"""Pre-flight cost estimation for planned provider calls.

This is deliberately separate from the provider implementations: the whole
point of T0.4 is to be able to add up the cost of a *plan* (e.g. "pull 500
ranked keywords for the client + 5 competitors, then run 25 SERP lookups for
competitor discovery") before a single paid call is made, and refuse the
plan up front if it would blow the project's budget.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from analyzer.budget.pricing import EndpointPricing, load_pricing_table
from analyzer.config import settings


@dataclass(frozen=True)
class PlannedCall:
    """One provider call a pipeline stage intends to make.

    `row_count` is whatever unit the endpoint's pricing is keyed on (a
    keyword-pull row cap, 1 for a single SERP query, etc.) — see
    analyzer/resources/dataforseo_pricing.yaml for what each endpoint expects.
    """

    endpoint: str
    row_count: int = 0
    label: str = ""


class UnknownEndpointError(KeyError):
    """Raised when a planned call names an endpoint with no pricing entry.

    Deliberately fails closed: an endpoint the estimator doesn't know the
    price of must not be silently treated as free.
    """


class CostEstimator:
    def __init__(self, pricing_config_path: Path | None = None):
        self._pricing: dict[str, EndpointPricing] = load_pricing_table(
            pricing_config_path or settings.dataforseo_pricing_config_path
        )

    def estimate_call(self, call: PlannedCall) -> float:
        try:
            pricing = self._pricing[call.endpoint]
        except KeyError as exc:
            raise UnknownEndpointError(
                f"No pricing entry for endpoint '{call.endpoint}' — add one to "
                "analyzer/resources/dataforseo_pricing.yaml before planning a call "
                "against it."
            ) from exc
        return pricing.estimate(call.row_count)

    def estimate_plan(self, calls: list[PlannedCall]) -> float:
        return sum(self.estimate_call(call) for call in calls)
