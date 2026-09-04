"""End-to-end pipeline test using synthetic, pre-seeded companies/people
(bypassing network discovery, which is a no-op in dry-run mode anyway) to
prove the NORMALIZE -> DEDUPLICATE -> VERIFY -> QUALIFY -> MANUAL REVIEW ->
EXPORT half of the pipeline is wired correctly end to end.
"""

from __future__ import annotations

import asyncio

import pandas as pd
import pytest

from src.config import AppConfig
from src.models import (
    Company,
    Evidence,
    NormalizedRole,
    Person,
    UkraineEvidenceType,
)
from src.orchestrator import Orchestrator


@pytest.fixture
def config(tmp_path):
    cfg = AppConfig.load()
    cfg.dry_run = True
    cfg.raw["output"] = {**cfg.raw.get("output", {}), "dir": str(tmp_path / "output")}
    cfg.cache_dir = str(tmp_path / "cache")
    cfg.checkpoint_dir = str(tmp_path / "checkpoints")
    cfg.raw.setdefault("run", {})["checkpoint_enabled"] = False
    return cfg


def _seed_qualifying_case(orchestrator: Orchestrator) -> None:
    company = Company(
        company_name="Sunrise Digital LLC",
        website="https://sunrisedigital.com",
        domain="sunrisedigital.com",
        city="Chicago",
        state="Illinois",
        employee_estimate=60,
        crawl_signals={
            "commercial_website": True,
            "marketing_department_exists": True,
            "is_ecommerce": True,
            "has_blog": True,
            "has_category_structure": True,
            "has_google_ads_tag": True,
            "has_conversion_tracking": True,
            "commercial_intent": True,
            "us_corporate_address": True,
            "hq_in_usa": True,
            "main_operating_market_usa": True,
            "multi_location": True,
            "multiple_products_or_services": True,
            "active_hiring": True,
            "international_presence": True,
            "high_value_services": True,
            "has_meta_pixel": True,
            "has_google_analytics": True,
        },
    )
    person = Person(
        full_name="Olena Petrenko",
        company_name=company.company_name,
        company_domain=company.domain,
        company_id=company.company_id,
        original_job_title="Chief Marketing Officer",
        normalized_role=NormalizedRole.CMO,
        city="Chicago",
        state="Illinois",
    )
    person.add_source_url("https://sunrisedigital.com/about")
    person.ukraine_connection.evidence.append(
        Evidence(
            source_url="https://sunrisedigital.com/about",
            evidence_type=UkraineEvidenceType.SELF_IDENTIFICATION,
            quote_fragment="Olena Petrenko is a Ukrainian entrepreneur and our CMO.",
            confidence=1.0,
        )
    )
    orchestrator.state.companies = [company]
    orchestrator.state.people = [person]


def test_full_downstream_pipeline_produces_qualified_account(config):
    orchestrator = Orchestrator(config)
    _seed_qualifying_case(orchestrator)

    orchestrator.normalize()
    orchestrator.deduplicate()
    orchestrator.verify_ukraine_connections()
    orchestrator.verify_us_companies()
    orchestrator.classify_company_types()
    orchestrator.qualify_accounts()
    orchestrator.finalize_confidence_and_manual_review()
    orchestrator.export()

    assert len(orchestrator.state.qualified_rows) == 1
    row = orchestrator.state.qualified_rows[0]
    assert row["company_name"] == "Sunrise Digital LLC"
    assert row["qualifying_person_name"] == "Olena Petrenko"
    assert row["qualifying_person_ukraine_connection_status"] == "verified"

    companies_csv = pd.read_csv(config.output_dir / "companies.csv")
    people_csv = pd.read_csv(config.output_dir / "people.csv")
    qualified_csv = pd.read_csv(config.output_dir / "qualified_accounts.csv")

    assert len(companies_csv) == 1
    assert len(people_csv) == 1
    assert len(qualified_csv) == 1
    assert people_csv.iloc[0]["ukraine_connection_status"] == "verified"
    assert people_csv.iloc[0]["normalized_role"] == "cmo"


def test_weak_evidence_person_goes_to_manual_review(config):
    orchestrator = Orchestrator(config)
    company = Company(company_name="Small Co", website="https://smallco.com", domain="smallco.com")
    person = Person(
        full_name="Someone Ambiguous",
        company_name=company.company_name,
        company_domain=company.domain,
        normalized_role=NormalizedRole.HEAD_OF_GROWTH,
    )
    # Below manual_review threshold entirely -> unknown, not manual_review;
    # give it exactly one weak page-level source to land in the band.
    person.ukraine_connection.evidence.append(
        Evidence(
            source_url="https://example.com/mention",
            evidence_type=UkraineEvidenceType.OTHER_PUBLIC_PROFESSIONAL_SOURCE,
            quote_fragment="brief mention",
            confidence=0.8,
        )
    )
    orchestrator.state.companies = [company]
    orchestrator.state.people = [person]

    orchestrator.normalize()
    orchestrator.deduplicate()
    orchestrator.verify_ukraine_connections()
    orchestrator.verify_us_companies()
    orchestrator.classify_company_types()
    orchestrator.qualify_accounts()
    orchestrator.finalize_confidence_and_manual_review()

    assert person.ukraine_connection.status.value == "manual_review"
    assert any(r.person == "Someone Ambiguous" for r in orchestrator.state.manual_review)
    # Not qualified for outbound (default outbound_statuses = ["verified"])
    assert orchestrator.state.qualified_rows == []


def test_full_run_via_run_method_with_no_sources(config, tmp_path):
    orchestrator = Orchestrator(config)
    state = asyncio.run(orchestrator.run(seed_path=None))
    assert state.companies == []
    assert (config.output_dir / "companies.csv").exists()
    assert (config.output_dir / "people.csv").exists()
    assert (config.output_dir / "qualified_accounts.csv").exists()
    assert (config.output_dir / "manual_review.csv").exists()
    assert (config.output_dir / "sources.csv").exists()
