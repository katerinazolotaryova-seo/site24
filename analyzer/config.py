"""Central configuration for the analyzer.

All settings are environment-driven (12-factor style) so the same code runs
against local Docker Compose services, CI, or a future hosted environment
without code changes. Values here are defaults for local development only —
never commit real credentials; use a local, untracked `.env` file.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_PRICING_CONFIG_PATH = PACKAGE_DIR / "resources" / "dataforseo_pricing.yaml"


class Settings(BaseSettings):
    """Application settings, overridable via `ANALYZER_*` environment variables.

    Example: `ANALYZER_DATABASE_URL=postgresql+psycopg://...` overrides `database_url`.
    """

    model_config = SettingsConfigDict(
        env_prefix="ANALYZER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database -----------------------------------------------------
    # Defaults to a local SQLite file so `python -m analyzer` works with zero
    # setup; docker-compose.yml points this at Postgres for anything beyond
    # a quick local check.
    database_url: str = "sqlite:///./analyzer_dev.db"

    # --- SEO data provider (DataForSEO) --------------------------------
    dataforseo_login: str | None = None
    dataforseo_password: str | None = None
    dataforseo_base_url: str = "https://api.dataforseo.com"

    # --- LLM ------------------------------------------------------------
    anthropic_api_key: str | None = None

    # --- API budget guardrail (see docs plan §4.1 / §10.2) --------------
    # $8/project is the agreed default ceiling; individual projects can
    # override it (api_budget_usd column on the project row), this is only
    # the value new projects are created with.
    default_api_budget_usd: float = Field(default=8.00, gt=0)

    # Planning-level DataForSEO cost estimates used by the pre-flight cost
    # estimator (analyzer.budget). MUST be checked against DataForSEO's
    # current price list before relying on this for real budget decisions.
    dataforseo_pricing_config_path: Path = DEFAULT_PRICING_CONFIG_PATH


settings = Settings()
