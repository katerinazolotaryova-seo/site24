from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from analyzer.budget.errors import BudgetExceededError
from analyzer.budget.estimator import CostEstimator, PlannedCall, UnknownEndpointError
from analyzer.budget.tracker import BudgetTracker
from analyzer.db.models import Project


def test_cost_estimator_computes_base_plus_per_row():
    estimator = CostEstimator()
    # ranked_keywords: base 0.0 + per_row 0.0002 * 500 = 0.10 (see resources/dataforseo_pricing.yaml)
    cost = estimator.estimate_call(PlannedCall(endpoint="ranked_keywords", row_count=500))
    assert cost == pytest.approx(0.10)


def test_cost_estimator_sums_a_plan():
    estimator = CostEstimator()
    calls = [
        PlannedCall(endpoint="domain_rank_overview", row_count=1),
        PlannedCall(endpoint="serp_organic_live_advanced", row_count=1),
    ]
    total = estimator.estimate_plan(calls)
    assert total == pytest.approx(0.01 + 0.003)


def test_cost_estimator_rejects_unknown_endpoint():
    estimator = CostEstimator()
    with pytest.raises(UnknownEndpointError):
        estimator.estimate_call(PlannedCall(endpoint="not_a_real_endpoint", row_count=1))


def test_budget_tracker_reserves_and_tracks_spend(db_session: Session, sample_project: Project):
    tracker = BudgetTracker(db_session, sample_project.id)
    assert tracker.remaining_budget_usd() == pytest.approx(8.00)

    tracker.check_and_reserve(2.50)
    assert tracker.remaining_budget_usd() == pytest.approx(5.50)
    assert sample_project.api_spend_usd == pytest.approx(2.50)


def test_budget_tracker_refuses_call_over_budget(db_session: Session, sample_project: Project):
    tracker = BudgetTracker(db_session, sample_project.id)
    tracker.check_and_reserve(7.00)

    with pytest.raises(BudgetExceededError) as excinfo:
        tracker.check_and_reserve(2.00)

    assert excinfo.value.project_id == sample_project.id
    assert excinfo.value.remaining_budget_usd == pytest.approx(1.00)
    # The refused reservation must not have been applied.
    assert sample_project.api_spend_usd == pytest.approx(7.00)


def test_budget_tracker_reconciles_actual_cost(db_session: Session, sample_project: Project):
    tracker = BudgetTracker(db_session, sample_project.id)
    tracker.check_and_reserve(1.00)  # pre-flight estimate
    # provider returned fewer rows than planned
    tracker.reconcile_actual_cost(reserved_cost_usd=1.00, actual_cost_usd=0.80)

    assert sample_project.api_spend_usd == pytest.approx(0.80)
    assert tracker.remaining_budget_usd() == pytest.approx(7.20)
