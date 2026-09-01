"""CLI entrypoint. Phase 0 scope: environment/schema bootstrapping and the
budget cost-estimator, exercised standalone. The full pipeline runner
(`analyzer run ...`, per plan §8 T4.6) lands in Phase 3.5, once the stages
it orchestrates exist.
"""

from __future__ import annotations

from pathlib import Path

import typer
from alembic import command
from alembic.config import Config

from analyzer import __version__
from analyzer.budget.estimator import CostEstimator, PlannedCall, UnknownEndpointError
from analyzer.logging_config import get_logger

REPO_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI_PATH = REPO_ROOT / "alembic.ini"

app = typer.Typer(
    help="Automated SEO Presale Analyzer — internal presale tooling. "
    "See docs/seo-presale-analyzer/ARCHITECTURE_AND_MVP_PLAN.md for scope and phases."
)
log = get_logger(__name__)


@app.command()
def version() -> None:
    """Print the analyzer version."""

    typer.echo(__version__)


@app.command("init-db")
def init_db() -> None:
    """Create/upgrade the database schema (`alembic upgrade head`)."""

    if not ALEMBIC_INI_PATH.exists():
        raise typer.BadParameter(f"alembic.ini not found at {ALEMBIC_INI_PATH}")
    cfg = Config(str(ALEMBIC_INI_PATH))
    command.upgrade(cfg, "head")
    typer.echo("Database schema is up to date.")


@app.command("estimate-cost")
def estimate_cost(
    ranked_keywords_rows: int = typer.Option(
        500, help="Row cap for the organic-keywords pull, per domain."
    ),
    domains: int = typer.Option(
        4, help="Client + competitor domains the keyword pull runs against."
    ),
    serp_queries: int = typer.Option(
        25, help="Number of SERP lookups planned for competitor discovery."
    ),
    include_domain_metrics: bool = typer.Option(
        True, help="Include one domain_rank_overview call per domain."
    ),
) -> None:
    """Estimate the DataForSEO cost of a planned MVP run, against the $8 default budget.

    This mirrors the pre-flight check `ProviderGateway`/`BudgetTracker` run
    automatically before a real pipeline call — useful for sanity-checking a
    project's planned row caps/query counts against the budget before
    running anything for real.
    """

    estimator = CostEstimator()
    calls: list[PlannedCall] = []

    if include_domain_metrics:
        calls += [PlannedCall(endpoint="domain_rank_overview", row_count=1)] * domains

    calls += [PlannedCall(endpoint="ranked_keywords", row_count=ranked_keywords_rows)] * domains
    calls += [PlannedCall(endpoint="serp_organic_live_advanced", row_count=1)] * serp_queries

    try:
        total = estimator.estimate_plan(calls)
    except UnknownEndpointError as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(f"Estimated cost: ${total:.4f}")
    typer.echo(f"  domain_rank_overview x{domains if include_domain_metrics else 0}")
    typer.echo(f"  ranked_keywords x{domains} (limit={ranked_keywords_rows} rows each)")
    typer.echo(f"  serp_organic_live_advanced x{serp_queries}")

    from analyzer.config import settings

    if total > settings.default_api_budget_usd:
        typer.secho(
            f"WARNING: exceeds the default ${settings.default_api_budget_usd:.2f} project budget "
            f"by ${total - settings.default_api_budget_usd:.4f}.",
            fg=typer.colors.RED,
        )
    else:
        typer.secho(
            f"Within the default ${settings.default_api_budget_usd:.2f} project budget "
            f"(${settings.default_api_budget_usd - total:.4f} headroom).",
            fg=typer.colors.GREEN,
        )


if __name__ == "__main__":
    app()
