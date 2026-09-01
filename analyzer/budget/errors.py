from __future__ import annotations


class BudgetExceededError(RuntimeError):
    """Raised when a planned (or actual) provider call would exceed a project's
    remaining API budget.

    Carries the numbers involved so callers (CLI, pipeline stages) can report
    exactly what was refused and why, per the plan's requirement that budget
    enforcement fail loudly *before* spending, not silently absorb overage.
    """

    def __init__(
        self,
        *,
        project_id: int,
        remaining_budget_usd: float,
        estimated_cost_usd: float,
        detail: str = "",
    ):
        self.project_id = project_id
        self.remaining_budget_usd = remaining_budget_usd
        self.estimated_cost_usd = estimated_cost_usd
        self.detail = detail
        message = (
            f"Project {project_id}: planned call costs ~${estimated_cost_usd:.4f} "
            f"but only ${remaining_budget_usd:.4f} of budget remains."
        )
        if detail:
            message = f"{message} ({detail})"
        super().__init__(message)
