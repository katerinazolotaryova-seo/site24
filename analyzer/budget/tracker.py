"""Per-project running spend tracking and enforcement.

Pattern: **reserve before calling, reconcile after**. `check_and_reserve`
immediately adds the estimated cost to the project's running spend (and
raises `BudgetExceededError` instead, if that would exceed the budget) —
so a call is never dispatched without room already having been counted
against the budget. Once the real provider response comes back with its
actual cost, `reconcile_actual_cost` corrects the running total from the
estimate to the real figure.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from analyzer.budget.errors import BudgetExceededError
from analyzer.db.models import Project


class BudgetTracker:
    def __init__(self, session: Session, project_id: int):
        self.session = session
        self.project_id = project_id

    def _get_project(self) -> Project:
        project = self.session.get(Project, self.project_id)
        if project is None:
            raise ValueError(f"No project with id={self.project_id}")
        return project

    def remaining_budget_usd(self) -> float:
        project = self._get_project()
        return project.api_budget_usd - project.api_spend_usd

    def check_and_reserve(self, estimated_cost_usd: float, *, detail: str = "") -> None:
        """Reserve `estimated_cost_usd` against the project's budget.

        Raises `BudgetExceededError` — and reserves nothing — if the project
        doesn't have that much budget left. Call this *before* making the
        provider request it corresponds to.
        """

        project = self._get_project()
        remaining = project.api_budget_usd - project.api_spend_usd
        if estimated_cost_usd > remaining:
            raise BudgetExceededError(
                project_id=self.project_id,
                remaining_budget_usd=remaining,
                estimated_cost_usd=estimated_cost_usd,
                detail=detail,
            )
        project.api_spend_usd += estimated_cost_usd
        self.session.flush()

    def reconcile_actual_cost(self, reserved_cost_usd: float, actual_cost_usd: float) -> None:
        """Correct the running spend from a pre-flight estimate to the real cost.

        Call this once the provider response is in hand. `actual_cost_usd`
        may be higher or lower than `reserved_cost_usd` was projected to be;
        either direction is applied as a delta against the running total.
        """

        project = self._get_project()
        project.api_spend_usd += actual_cost_usd - reserved_cost_usd
        self.session.flush()
