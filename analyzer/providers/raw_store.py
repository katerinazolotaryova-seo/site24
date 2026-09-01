"""Persists a `RawProviderResponse` to the `seo_metrics_raw` table.

Kept as a standalone function (rather than a method on the provider or the
ORM model) so it's the single place that turns "a response came back from a
vendor" into "a row of raw, never-mutated evidence" — every provider call
must go through this, regardless of which vendor answered it.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from analyzer.db.models import SeoMetricsRaw
from analyzer.providers.base import RawProviderResponse


def persist_raw_response(session: Session, domain_id: int, response: RawProviderResponse) -> SeoMetricsRaw:
    row = SeoMetricsRaw(
        domain_id=domain_id,
        provider=response.provider,
        endpoint=response.endpoint,
        request_params=response.request_params,
        raw_response=response.raw_response,
        estimated_cost_usd=response.estimated_cost_usd,
        fetched_at=response.fetched_at,
    )
    session.add(row)
    session.flush()
    return row
