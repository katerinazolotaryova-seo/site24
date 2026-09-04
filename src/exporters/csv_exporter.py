"""Writes the five CSV outputs (companies, people, qualified_accounts,
manual_review, sources) to the configured output directory, using pandas
so column order and encoding stay consistent.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.models import Company, DiscoverySource, ManualReviewRecord, Person

COMPANY_COLUMNS = [
    "company_name", "domain", "website", "city", "state", "country", "industry",
    "employee_estimate", "company_type", "company_source", "us_presence_status",
    "account_score", "seo_score", "ppc_score", "discovery_date",
]

PEOPLE_COLUMNS = [
    "full_name", "company_name", "company_domain", "original_job_title", "normalized_role",
    "city", "state", "linkedin", "telegram", "instagram", "facebook", "email", "phone",
    "person_source_urls", "ukraine_connection_status", "ukraine_connection_type",
    "ukraine_connection_score", "us_role_status", "person_confidence", "manual_review_required",
]

QUALIFIED_ACCOUNT_COLUMNS = [
    "company_name", "domain", "website", "city", "state", "country", "industry",
    "employee_estimate", "company_type", "us_presence_status", "account_score", "seo_score",
    "ppc_score", "qualifying_person_name", "qualifying_person_role",
    "qualifying_person_ukraine_connection_status", "qualifying_person_ukraine_connection_score",
    "qualifying_person_contact_channel", "discovery_date",
]

MANUAL_REVIEW_COLUMNS = [
    "person", "company", "candidate_url", "reason", "person_confidence",
    "ukraine_connection_score", "conflicting_evidence", "source_urls",
]

SOURCES_COLUMNS = [
    "source_id", "source_name", "source_url", "source_type", "discovered_via",
    "discovered_at", "pages_classified",
]


def _field_value_str(fv) -> str:
    return fv.value if fv else ""


def company_to_row(c: Company) -> dict:
    return {
        "company_name": c.company_name,
        "domain": c.domain or "",
        "website": c.website or "",
        "city": c.city or "",
        "state": c.state or "",
        "country": c.country,
        "industry": c.industry or "",
        "employee_estimate": c.employee_estimate if c.employee_estimate is not None else "",
        "company_type": c.company_type.value,
        "company_source": ";".join(c.company_source),
        "us_presence_status": c.us_presence_status.value,
        "account_score": c.account_score,
        "seo_score": c.seo_score,
        "ppc_score": c.ppc_score,
        "discovery_date": c.discovery_date.isoformat(),
    }


def person_to_row(p: Person) -> dict:
    return {
        "full_name": p.full_name,
        "company_name": p.company_name or "",
        "company_domain": p.company_domain or "",
        "original_job_title": p.original_job_title or "",
        "normalized_role": p.normalized_role.value,
        "city": p.city or "",
        "state": p.state or "",
        "linkedin": _field_value_str(p.linkedin),
        "telegram": _field_value_str(p.telegram),
        "instagram": _field_value_str(p.instagram),
        "facebook": _field_value_str(p.facebook),
        "email": _field_value_str(p.email),
        "phone": _field_value_str(p.phone),
        "person_source_urls": ";".join(p.person_source_urls),
        "ukraine_connection_status": p.ukraine_connection.status.value,
        "ukraine_connection_type": p.ukraine_connection.connection_type.value if p.ukraine_connection.connection_type else "",
        "ukraine_connection_score": p.ukraine_connection.score,
        "us_role_status": p.us_role_status.value,
        "person_confidence": p.person_confidence,
        "manual_review_required": p.manual_review_required,
    }


def manual_review_to_row(r: ManualReviewRecord) -> dict:
    return {
        "person": r.person or "",
        "company": r.company or "",
        "candidate_url": r.candidate_url or "",
        "reason": r.reason,
        "person_confidence": r.person_confidence,
        "ukraine_connection_score": r.ukraine_connection_score,
        "conflicting_evidence": r.conflicting_evidence or "",
        "source_urls": ";".join(r.source_urls),
    }


def source_to_row(s: DiscoverySource) -> dict:
    return {
        "source_id": s.source_id,
        "source_name": s.source_name,
        "source_url": s.source_url,
        "source_type": s.source_type,
        "discovered_via": s.discovered_via or "",
        "discovered_at": s.discovered_at.isoformat(),
        "pages_classified": ";".join(s.pages_classified),
    }


def _write_csv(rows: list[dict], columns: list[str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=columns)
    df.to_csv(path, index=False)


def write_companies_csv(companies: list[Company], path: str | Path) -> None:
    _write_csv([company_to_row(c) for c in companies], COMPANY_COLUMNS, Path(path))


def write_people_csv(people: list[Person], path: str | Path) -> None:
    _write_csv([person_to_row(p) for p in people], PEOPLE_COLUMNS, Path(path))


def write_qualified_accounts_csv(rows: list[dict], path: str | Path) -> None:
    _write_csv(rows, QUALIFIED_ACCOUNT_COLUMNS, Path(path))


def write_manual_review_csv(records: list[ManualReviewRecord], path: str | Path) -> None:
    _write_csv([manual_review_to_row(r) for r in records], MANUAL_REVIEW_COLUMNS, Path(path))


def write_sources_csv(sources: list[DiscoverySource], path: str | Path) -> None:
    _write_csv([source_to_row(s) for s in sources], SOURCES_COLUMNS, Path(path))
