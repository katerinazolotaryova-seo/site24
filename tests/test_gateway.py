"""ProviderGateway ties T0.3 (persist raw responses) and T0.4 (budget
guardrail) together: every provider call must be pre-flight-checked against
the project's budget *before* it happens, and persisted to seo_metrics_raw
afterwards.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from analyzer.budget.errors import BudgetExceededError
from analyzer.budget.estimator import PlannedCall
from analyzer.db.models import Domain, Project, SeoMetricsRaw
from analyzer.providers.base import RawProviderResponse
from analyzer.providers.gateway import ProviderGateway


def _fake_response(estimated_cost_usd: float = 0.01) -> RawProviderResponse:
    return RawProviderResponse(
        provider="dataforseo",
        endpoint="domain_rank_overview",
        request_params={"target": "acme-roofing.example"},
        raw_response={"ok": True},
        estimated_cost_usd=estimated_cost_usd,
        fetched_at=datetime.now(UTC),
    )


def test_gateway_persists_raw_response_and_spends_budget(
    db_session: Session, sample_project: Project, sample_domain: Domain
):
    gateway = ProviderGateway(session=db_session, project_id=sample_project.id, domain_id=sample_domain.id)
    calls_made = []

    def fn():
        calls_made.append(1)
        return _fake_response(0.01)

    raw_row = gateway.call(PlannedCall(endpoint="domain_rank_overview", row_count=1), fn)

    assert len(calls_made) == 1
    assert isinstance(raw_row, SeoMetricsRaw)
    assert raw_row.provider == "dataforseo"
    assert raw_row.domain_id == sample_domain.id
    assert sample_project.api_spend_usd == pytest.approx(0.01)
    assert gateway.remaining_budget_usd() == pytest.approx(8.00 - 0.01)


def test_gateway_refuses_call_over_budget_without_calling_provider(
    db_session: Session, sample_project: Project, sample_domain: Domain
):
    sample_project.api_budget_usd = 0.005  # smaller than domain_rank_overview's 0.01 base cost
    db_session.flush()

    gateway = ProviderGateway(session=db_session, project_id=sample_project.id, domain_id=sample_domain.id)
    calls_made = []

    def fn():
        calls_made.append(1)  # should never run
        return _fake_response(0.01)

    with pytest.raises(BudgetExceededError):
        gateway.call(PlannedCall(endpoint="domain_rank_overview", row_count=1), fn)

    assert calls_made == [], "the provider must not be called once the pre-flight check fails"
    assert (
        db_session.query(SeoMetricsRaw).count() == 0
    ), "a refused call must not persist a raw row"


def test_gateway_reconciles_when_actual_cost_differs_from_estimate(
    db_session: Session, sample_project: Project, sample_domain: Domain
):
    gateway = ProviderGateway(session=db_session, project_id=sample_project.id, domain_id=sample_domain.id)

    # Planned as a 500-row pull (estimate ~0.10 for ranked_keywords) but the
    # provider only actually returned rows worth $0.04 — spend should land on
    # the real figure, not the pre-flight estimate.
    actual_response = RawProviderResponse(
        provider="dataforseo",
        endpoint="ranked_keywords",
        request_params={},
        raw_response={},
        estimated_cost_usd=0.04,
        fetched_at=datetime.now(UTC),
    )
    gateway.call(PlannedCall(endpoint="ranked_keywords", row_count=500), lambda: actual_response)

    assert sample_project.api_spend_usd == pytest.approx(0.04)
