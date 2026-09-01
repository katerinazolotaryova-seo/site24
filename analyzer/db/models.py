"""ORM models for the MVP schema.

Mirrors docs/seo-presale-analyzer/ARCHITECTURE_AND_MVP_PLAN.md §6 (Database
schema). Tables marked `[prov.]` in that document carry explicit provenance
columns (source provider/endpoint, fetched/computed timestamps, and a
back-reference to the raw record a normalized value was derived from) so
every number in a report can be traced back to where it came from (brief
§25).

Only MVP-scope tables are defined here. Post-MVP tables sketched in the plan
(`page_blocks`, `backlink_profiles`, `referring_domains`, `eeat_signals`,
full `serp_results`) are deferred to the phases that need them (§9 of the
plan) and are not created by this module's migration.

Enums are stored as plain strings with a `native_enum=False` SQLAlchemy
`Enum`, not native Postgres enum types — this keeps adding a new value a
plain data migration instead of an `ALTER TYPE`, which matters for a schema
that is still expected to evolve through the MVP phases.
"""

from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import (
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from analyzer.db.base import Base
from analyzer.db.types import PortableJSONB


def _enum(python_enum: type[enum.Enum], **kwargs):
    return Enum(python_enum, native_enum=False, validate_strings=True, **kwargs)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class WebsiteType(str, enum.Enum):
    SERVICES = "services"
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    OTHER = "other"


class DomainRole(str, enum.Enum):
    CLIENT = "client"
    COMPETITOR = "competitor"


class CompetitorSource(str, enum.Enum):
    USER_PROVIDED = "user_provided"
    DISCOVERED = "discovered"


class CrawlStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PageTypeMethod(str, enum.Enum):
    RULE = "rule"
    LLM = "llm"


class LinkType(str, enum.Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"


class IntentMethod(str, enum.Enum):
    PROVIDER = "provider"
    HEURISTIC = "heuristic"
    LLM = "llm"


class KeywordIntent(str, enum.Enum):
    COMMERCIAL = "commercial"
    TRANSACTIONAL = "transactional"
    INFORMATIONAL = "informational"
    NAVIGATIONAL = "navigational"


class OpportunityStatus(str, enum.Enum):
    COVERED = "covered"
    WEAK = "weak"
    MISSING = "missing"


class FindingSeverity(str, enum.Enum):
    CRITICAL = "critical"
    NOTABLE = "notable"
    MINOR = "minor"


class OpportunityType(str, enum.Enum):
    TRAFFIC_GAP = "traffic_gap"
    SEMANTIC_GAP = "semantic_gap"
    COMMERCIAL_PAGE_GAP = "commercial_page_gap"
    PAGE_STRUCTURE_GAP = "page_structure_gap"
    CONTENT_GAP = "content_gap"
    BACKLINK_GAP = "backlink_gap"
    EEAT_GAP = "eeat_gap"
    TECHNICAL_GAP = "technical_gap"
    QUICK_WINS = "quick_wins"


class LlmRunStage(str, enum.Enum):
    INTERPRETATION = "interpretation"
    TALKING_POINTS = "talking_points"
    PAGE_STRUCTURE = "page_structure"
    EEAT = "eeat"


class ValidationStatus(str, enum.Enum):
    PASSED = "passed"
    REGENERATED = "regenerated"
    FALLBACK = "fallback"


# ---------------------------------------------------------------------------
# Core project / domain / crawl
# ---------------------------------------------------------------------------


class Project(Base):
    """One presale analysis engagement for one prospect domain."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    domain: Mapped[str] = mapped_column(String(255))
    target_country: Mapped[str] = mapped_column(String(2))
    target_language: Mapped[str] = mapped_column(String(10))
    business_type: Mapped[str] = mapped_column(String(255))
    website_type: Mapped[WebsiteType] = mapped_column(_enum(WebsiteType))
    priority_services: Mapped[list | None] = mapped_column(PortableJSONB, nullable=True)

    # API budget guardrail (plan §4.1 / §10.2): $8 default ceiling per
    # project, enforced by analyzer.budget before any paid provider call.
    api_budget_usd: Mapped[float] = mapped_column(Float, default=8.00)
    api_spend_usd: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    domains: Mapped[list[Domain]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Domain(Base):
    """Client or competitor hostname within a project."""

    __tablename__ = "domains"
    __table_args__ = (UniqueConstraint("project_id", "hostname", name="uq_domain_project_hostname"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    hostname: Mapped[str] = mapped_column(String(255))
    role: Mapped[DomainRole] = mapped_column(_enum(DomainRole))
    competitor_source: Mapped[CompetitorSource | None] = mapped_column(_enum(CompetitorSource), nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    added_at: Mapped[datetime] = mapped_column(server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="domains")


class Crawl(Base):
    __tablename__ = "crawls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"))
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[CrawlStatus] = mapped_column(_enum(CrawlStatus), default=CrawlStatus.PENDING)
    page_budget: Mapped[int] = mapped_column(Integer, default=300)
    pages_crawled: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crawl_id: Mapped[int] = mapped_column(ForeignKey("crawls.id"))
    url: Mapped[str] = mapped_column(Text)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    indexable: Mapped[bool | None] = mapped_column(nullable=True)
    robots_directives: Mapped[dict | None] = mapped_column(PortableJSONB, nullable=True)
    canonical: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    h1: Mapped[str | None] = mapped_column(Text, nullable=True)
    h2: Mapped[list | None] = mapped_column(PortableJSONB, nullable=True)
    h3: Mapped[list | None] = mapped_column(PortableJSONB, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    page_type_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    page_type_method: Mapped[PageTypeMethod | None] = mapped_column(_enum(PageTypeMethod), nullable=True)
    page_depth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    structured_data: Mapped[dict | list | None] = mapped_column(PortableJSONB, nullable=True)
    breadcrumbs: Mapped[dict | list | None] = mapped_column(PortableJSONB, nullable=True)
    pagination: Mapped[dict | None] = mapped_column(PortableJSONB, nullable=True)
    hreflang: Mapped[dict | list | None] = mapped_column(PortableJSONB, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_html_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    rendered_with_js: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class PageLink(Base):
    __tablename__ = "page_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"))
    target_url: Mapped[str] = mapped_column(Text)
    link_type: Mapped[LinkType] = mapped_column(_enum(LinkType))
    anchor_text: Mapped[str | None] = mapped_column(Text, nullable=True)


class PageImage(Base):
    __tablename__ = "page_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"))
    src: Mapped[str] = mapped_column(Text)
    alt_text: Mapped[str | None] = mapped_column(Text, nullable=True)


# ---------------------------------------------------------------------------
# SEO data provider: raw + normalized
# ---------------------------------------------------------------------------


class SeoMetricsRaw(Base):
    """Verbatim provider API responses. Never mutated after insert.

    This is the "RAW DATA" layer in the pipeline (plan §2/§24): normalized
    tables below always carry a `source_raw_id` back to a row here, so the
    whole analysis is recomputable without re-purchasing provider data.
    """

    __tablename__ = "seo_metrics_raw"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"))
    provider: Mapped[str] = mapped_column(String(50))
    endpoint: Mapped[str] = mapped_column(String(255))
    request_params: Mapped[dict] = mapped_column(PortableJSONB)
    raw_response: Mapped[dict | list] = mapped_column(PortableJSONB)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    fetched_at: Mapped[datetime] = mapped_column(server_default=func.now())


class DomainMetrics(Base):
    __tablename__ = "domain_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"))
    date: Mapped[date] = mapped_column()
    organic_traffic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    organic_keywords: Mapped[int | None] = mapped_column(Integer, nullable=True)
    top3: Mapped[int | None] = mapped_column(Integer, nullable=True)
    top10: Mapped[int | None] = mapped_column(Integer, nullable=True)
    top20: Mapped[int | None] = mapped_column(Integer, nullable=True)
    top100: Mapped[int | None] = mapped_column(Integer, nullable=True)
    traffic_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    branded_keywords: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nonbranded_keywords: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_raw_id: Mapped[int | None] = mapped_column(ForeignKey("seo_metrics_raw.id"), nullable=True)


# ---------------------------------------------------------------------------
# Keywords / clustering
# ---------------------------------------------------------------------------


class Keyword(Base):
    __tablename__ = "keywords"
    __table_args__ = (
        UniqueConstraint("project_id", "text_normalized", "locale", name="uq_keyword_project_text_locale"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    text_normalized: Mapped[str] = mapped_column(String(500))
    locale: Mapped[str] = mapped_column(String(10))
    search_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cpc: Mapped[float | None] = mapped_column(Float, nullable=True)
    competition: Mapped[float | None] = mapped_column(Float, nullable=True)
    intent: Mapped[KeywordIntent | None] = mapped_column(_enum(KeywordIntent), nullable=True)
    intent_method: Mapped[IntentMethod | None] = mapped_column(_enum(IntentMethod), nullable=True)


class KeywordPosition(Base):
    __tablename__ = "keyword_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"))
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"))
    url: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer)
    date: Mapped[date] = mapped_column()
    source_raw_id: Mapped[int | None] = mapped_column(ForeignKey("seo_metrics_raw.id"), nullable=True)


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String(255))
    intent: Mapped[KeywordIntent | None] = mapped_column(_enum(KeywordIntent), nullable=True)
    total_search_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clustering_method: Mapped[str] = mapped_column(String(50))
    clustering_version: Mapped[str] = mapped_column(String(20))


class ClusterKeyword(Base):
    __tablename__ = "cluster_keywords"

    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id"), primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), primary_key=True)


class ClusterUrlMap(Base):
    __tablename__ = "cluster_url_map"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id"))
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"))
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    best_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    opportunity_status: Mapped[OpportunityStatus] = mapped_column(_enum(OpportunityStatus))


# ---------------------------------------------------------------------------
# Technical findings / opportunities / scoring
# ---------------------------------------------------------------------------


class TechnicalFinding(Base):
    __tablename__ = "technical_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crawl_id: Mapped[int] = mapped_column(ForeignKey("crawls.id"))
    issue_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[FindingSeverity] = mapped_column(_enum(FindingSeverity))
    affected_url_count: Mapped[int] = mapped_column(Integer)
    affected_urls_sample: Mapped[list | None] = mapped_column(PortableJSONB, nullable=True)
    description: Mapped[str] = mapped_column(Text)
    materiality_pct: Mapped[float | None] = mapped_column(Float, nullable=True)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    type: Mapped[OpportunityType] = mapped_column(_enum(OpportunityType))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict | list | None] = mapped_column(PortableJSONB, nullable=True)
    impact: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    effort: Mapped[int | None] = mapped_column(Integer, nullable=True)
    business_relevance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    scoring_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


# ---------------------------------------------------------------------------
# Reports / sales talking points / LLM runs
# ---------------------------------------------------------------------------


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    generated_at: Mapped[datetime] = mapped_column(server_default=func.now())
    pipeline_version: Mapped[str] = mapped_column(String(20))
    sections: Mapped[dict] = mapped_column(PortableJSONB)
    file_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_run_id: Mapped[int | None] = mapped_column(ForeignKey("llm_runs.id"), nullable=True)


class SalesTalkingPoints(Base):
    __tablename__ = "sales_talking_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"))
    primary_angle: Mapped[str] = mapped_column(Text)
    supporting_arguments: Mapped[list] = mapped_column(PortableJSONB)
    quick_win_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    what_to_sell: Mapped[list] = mapped_column(PortableJSONB)


class LlmRun(Base):
    """One LLM call, kept for auditability of every generated claim.

    `validation_status` records whether the grounding validator (plan §1
    risk #8) accepted the output as-is, forced a regeneration, or fell back
    to templated text.
    """

    __tablename__ = "llm_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    stage: Mapped[LlmRunStage] = mapped_column(_enum(LlmRunStage))
    model: Mapped[str] = mapped_column(String(100))
    input_payload: Mapped[dict] = mapped_column(PortableJSONB)
    output_payload: Mapped[dict] = mapped_column(PortableJSONB)
    validation_status: Mapped[ValidationStatus] = mapped_column(_enum(ValidationStatus))
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
