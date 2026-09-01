from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from analyzer.db import models  # noqa: F401  (registers tables on Base.metadata)
from analyzer.db.base import Base
from analyzer.db.models import Domain, DomainRole, Project, WebsiteType


@pytest.fixture()
def db_session() -> Session:
    """A fresh in-memory SQLite database per test, schema created from the ORM
    models directly (not via Alembic — Alembic's own migration is exercised
    separately in test_migrations.py)."""

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def sample_project(db_session: Session) -> Project:
    project = Project(
        name="Acme Roofing — presale",
        domain="acme-roofing.example",
        target_country="us",
        target_language="en",
        business_type="roofing contractor",
        website_type=WebsiteType.SERVICES,
        api_budget_usd=8.00,
    )
    db_session.add(project)
    db_session.flush()
    return project


@pytest.fixture()
def sample_domain(db_session: Session, sample_project: Project) -> Domain:
    domain = Domain(
        project_id=sample_project.id,
        hostname="acme-roofing.example",
        role=DomainRole.CLIENT,
    )
    db_session.add(domain)
    db_session.flush()
    return domain
