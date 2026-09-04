"""Configuration loading for the Ukraine-US Leads system.

Loads config/config.yaml (+ roles/states/cities/seed/ukraine_companies) and
overlays environment variables (via python-dotenv) for secrets and runtime
toggles. Everything is exposed through a single `AppConfig` object so the
rest of the codebase never touches raw dicts.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    try:
        return int(v)
    except ValueError:
        return default


@dataclass
class AppConfig:
    raw: dict = field(default_factory=dict)
    roles: dict = field(default_factory=dict)
    states: list[str] = field(default_factory=list)
    cities: list[dict] = field(default_factory=list)
    ukraine_companies: list[str] = field(default_factory=list)

    # environment-derived overrides
    dry_run: bool = True
    search_backend: str = "none"
    search_api_key: Optional[str] = None
    search_cse_id: Optional[str] = None
    search_rps: int = 1
    hunter_api_key: Optional[str] = None
    hunter_enabled: bool = False
    hunter_credit_limit: int = 100
    apollo_api_key: Optional[str] = None
    apollo_enabled: bool = False
    apollo_credit_limit: int = 100
    log_level: str = "INFO"
    cache_dir: str = ".cache"
    checkpoint_dir: str = ".checkpoints"

    @classmethod
    def load(cls, config_dir: Path = CONFIG_DIR, env_file: Optional[Path] = None) -> "AppConfig":
        load_dotenv(dotenv_path=env_file or (PROJECT_ROOT / ".env"))

        raw = _load_yaml(config_dir / "config.yaml")
        roles = _load_yaml(config_dir / "roles.yaml")
        states_doc = _load_yaml(config_dir / "states.yaml")
        cities_doc = _load_yaml(config_dir / "cities.yaml")
        ukraine_companies_doc = _load_yaml(config_dir / "ukraine_companies.yaml")

        cfg = cls(
            raw=raw,
            roles=roles,
            states=states_doc.get("states", []),
            cities=cities_doc.get("cities", []),
            ukraine_companies=ukraine_companies_doc.get("companies", []),
        )

        run_cfg = raw.get("run", {})
        providers_cfg = raw.get("providers", {})

        cfg.dry_run = _env_bool("DRY_RUN", run_cfg.get("dry_run", True))
        cfg.search_backend = os.getenv(
            "SEARCH_PROVIDER_BACKEND", providers_cfg.get("search", {}).get("backend", "none")
        )
        cfg.search_api_key = os.getenv("SEARCH_PROVIDER_API_KEY") or None
        cfg.search_cse_id = os.getenv("SEARCH_PROVIDER_CSE_ID") or None
        cfg.search_rps = _env_int("SEARCH_PROVIDER_RPS", providers_cfg.get("search", {}).get("rps", 1))

        cfg.hunter_api_key = os.getenv("HUNTER_API_KEY") or None
        cfg.hunter_enabled = _env_bool("HUNTER_ENABLED", providers_cfg.get("hunter", {}).get("enabled", False))
        cfg.hunter_credit_limit = _env_int(
            "HUNTER_MONTHLY_CREDIT_LIMIT", providers_cfg.get("hunter", {}).get("monthly_credit_limit", 100)
        )

        cfg.apollo_api_key = os.getenv("APOLLO_API_KEY") or None
        cfg.apollo_enabled = _env_bool("APOLLO_ENABLED", providers_cfg.get("apollo", {}).get("enabled", False))
        cfg.apollo_credit_limit = _env_int(
            "APOLLO_MONTHLY_CREDIT_LIMIT", providers_cfg.get("apollo", {}).get("monthly_credit_limit", 100)
        )

        cfg.log_level = os.getenv("LOG_LEVEL", raw.get("logging", {}).get("level", "INFO"))
        cfg.cache_dir = os.getenv("CACHE_DIR", run_cfg.get("cache_dir", ".cache"))
        cfg.checkpoint_dir = os.getenv("CHECKPOINT_DIR", run_cfg.get("checkpoint_dir", ".checkpoints"))

        # Real API keys imply the provider is meaningfully enabled even if
        # dry_run is left true in config.yaml; conversely dry_run=true always
        # forces mock behavior regardless of keys (safety default).
        return cfg

    # -- convenience accessors -------------------------------------------------

    def get(self, path: str, default: Any = None) -> Any:
        """Dotted-path getter into the raw config, e.g. cfg.get('qualification.min_account_score')."""
        node: Any = self.raw
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    @property
    def output_dir(self) -> Path:
        return PROJECT_ROOT / self.get("output.dir", "output")

    @property
    def max_records(self) -> Optional[int]:
        return self.get("run.max_records")

    @property
    def qualification_weights(self) -> dict:
        return self.get("qualification.weights", {})

    @property
    def priority_roles(self) -> list[str]:
        return self.roles.get("priority_roles", [])

    @property
    def title_patterns(self) -> dict:
        return self.roles.get("title_patterns", {})


_default_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    global _default_config
    if _default_config is None:
        _default_config = AppConfig.load()
    return _default_config
