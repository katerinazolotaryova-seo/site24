"""Exercises the actual Alembic migration (not just `Base.metadata.create_all`),
per T0.2's acceptance criteria: `alembic upgrade head` must create every MVP
table on its own.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

REPO_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI_PATH = REPO_ROOT / "alembic.ini"

EXPECTED_TABLES = {
    "projects",
    "domains",
    "crawls",
    "pages",
    "page_links",
    "page_images",
    "seo_metrics_raw",
    "domain_metrics",
    "keywords",
    "keyword_positions",
    "clusters",
    "cluster_keywords",
    "cluster_url_map",
    "technical_findings",
    "opportunities",
    "reports",
    "sales_talking_points",
    "llm_runs",
}


def test_alembic_upgrade_head_creates_all_mvp_tables(tmp_path, monkeypatch):
    db_path = tmp_path / "migration_test.db"
    database_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("ANALYZER_DATABASE_URL", database_url)

    cfg = Config(str(ALEMBIC_INI_PATH))
    command.upgrade(cfg, "head")

    engine = create_engine(database_url, future=True)
    tables = set(inspect(engine).get_table_names())
    engine.dispose()

    missing = EXPECTED_TABLES - tables
    assert not missing, f"alembic upgrade head did not create: {missing}"
