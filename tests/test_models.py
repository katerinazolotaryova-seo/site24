from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from analyzer.db.models import (
    Domain,
    DomainMetrics,
    DomainRole,
    Project,
    SeoMetricsRaw,
    WebsiteType,
)


def test_project_roundtrip(db_session: Session):
    project = Project(
        name="Test co",
        domain="test.example",
        target_country="us",
        target_language="en",
        business_type="saas",
        website_type=WebsiteType.SAAS,
    )
    db_session.add(project)
    db_session.commit()

    fetched = db_session.get(Project, project.id)
    assert fetched is not None
    assert fetched.website_type == WebsiteType.SAAS
    # Provenance/budget defaults from the plan (§10.2): $8 ceiling, zero spend.
    assert fetched.api_budget_usd == 8.00
    assert fetched.api_spend_usd == 0.0


def test_domain_metrics_traces_back_to_raw_response(
    db_session: Session, sample_project: Project, sample_domain: Domain
):
    raw = SeoMetricsRaw(
        domain_id=sample_domain.id,
        provider="dataforseo",
        endpoint="domain_rank_overview",
        request_params={"target": sample_domain.hostname},
        raw_response={"tasks": []},
        estimated_cost_usd=0.01,
    )
    db_session.add(raw)
    db_session.flush()

    metrics = DomainMetrics(
        domain_id=sample_domain.id,
        date=date(2026, 8, 1),
        organic_traffic=3200,
        organic_keywords=412,
        source_raw_id=raw.id,
    )
    db_session.add(metrics)
    db_session.commit()

    fetched = db_session.get(DomainMetrics, metrics.id)
    assert fetched.source_raw_id == raw.id
    source = db_session.get(SeoMetricsRaw, fetched.source_raw_id)
    assert source.provider == "dataforseo"


def test_domain_unique_per_project(db_session: Session, sample_project: Project):
    db_session.add(Domain(project_id=sample_project.id, hostname="dup.example", role=DomainRole.CLIENT))
    db_session.commit()

    db_session.add(Domain(project_id=sample_project.id, hostname="dup.example", role=DomainRole.COMPETITOR))
    try:
        db_session.commit()
        assert False, "expected a uniqueness violation"
    except Exception:
        db_session.rollback()
