"""Ties the provider abstraction, the budget guardrail, and raw storage together.

`ProviderGateway.call` is the *only* sanctioned way pipeline code should
invoke a `SEODataProvider` method. It:

1. Estimates the call's cost (`PlannedCall` -> `CostEstimator`) and reserves
   that amount against the project's budget *before* the call happens,
   raising `BudgetExceededError` (no network call made) if it would exceed
   the ceiling — this is what makes the $8/project budget (plan §10.2) an
   enforced constraint instead of a documented intention.
2. Executes the call.
3. Reconciles the reservation against the response's actual estimated cost
   (the two can differ if, say, a provider returns fewer rows than the
   requested limit).
4. Persists the raw response to `seo_metrics_raw` before returning — so
   normalization always has a raw record to point `source_raw_id` at.

Pipeline stages therefore never call a `SEODataProvider` method directly;
they go through a `ProviderGateway` instance bound to the current project
and domain.
"""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from analyzer.budget.estimator import CostEstimator, PlannedCall
from analyzer.budget.tracker import BudgetTracker
from analyzer.db.models import SeoMetricsRaw
from analyzer.providers.base import RawProviderResponse
from analyzer.providers.raw_store import persist_raw_response


class ProviderGateway:
    def __init__(
        self,
        *,
        session: Session,
        project_id: int,
        domain_id: int,
        cost_estimator: CostEstimator | None = None,
        budget_tracker: BudgetTracker | None = None,
    ):
        self.session = session
        self.project_id = project_id
        self.domain_id = domain_id
        self._cost_estimator = cost_estimator or CostEstimator()
        self._budget_tracker = budget_tracker or BudgetTracker(session, project_id)

    def call(self, planned: PlannedCall, fn: Callable[[], RawProviderResponse]) -> SeoMetricsRaw:
        """Run one budgeted, persisted provider call.

        `planned` must describe the same endpoint/row_count the underlying
        provider call in `fn` will report back — the estimator uses it to
        reserve budget *before* `fn` runs. `fn` is typically a lambda
        wrapping a single `SEODataProvider` method call, e.g.:

            gateway.call(
                PlannedCall(endpoint="domain_rank_overview", row_count=1),
                lambda: provider.get_domain_metrics(domain, country="US", language="en"),
            )
        """

        estimated_cost = self._cost_estimator.estimate_call(planned)
        self._budget_tracker.check_and_reserve(estimated_cost, detail=planned.label or planned.endpoint)

        response = fn()

        self._budget_tracker.reconcile_actual_cost(estimated_cost, response.estimated_cost_usd)
        return persist_raw_response(self.session, self.domain_id, response)

    def remaining_budget_usd(self) -> float:
        return self._budget_tracker.remaining_budget_usd()
