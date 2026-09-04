"""Core data models for the Ukraine-US Leads discovery system.

These are the canonical in-memory representations that every stage of the
pipeline (discovery -> crawling -> verification -> qualification ->
enrichment -> export) reads and writes. CSV/JSONL export shapes are derived
from these models in src/exporters/.

Design notes
------------
* Every "fact" that can be disputed (an email, a Ukraine-connection claim, a
  social handle) is wrapped in `Evidence`/`FieldValue` so we always know
  *where* it came from and *how confident* we are (Stage 20: source
  tracking). We deliberately do not store long quotes -- only short
  fragments (<= ~200 chars) for auditability.
* Enums are plain `str` subclasses so they serialize cleanly to CSV/JSON
  without needing `.value` everywhere.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _new_id() -> str:
    return uuid.uuid4().hex[:16]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class NormalizedRole(str, Enum):
    FOUNDER = "founder"
    CO_FOUNDER = "co_founder"
    OWNER = "owner"
    CEO = "ceo"

    CMO = "cmo"
    VP_MARKETING = "vp_marketing"
    HEAD_OF_MARKETING = "head_of_marketing"
    MARKETING_DIRECTOR = "marketing_director"
    HEAD_OF_GROWTH = "head_of_growth"
    HEAD_OF_DIGITAL = "head_of_digital"

    HEAD_OF_SEO = "head_of_seo"
    HEAD_OF_PPC = "head_of_ppc"
    HEAD_OF_PERFORMANCE = "head_of_performance"

    MARKETING_MANAGER = "marketing_manager"
    GROWTH_MANAGER = "growth_manager"

    OTHER = "other"


FOUNDER_ROLES = {
    NormalizedRole.FOUNDER,
    NormalizedRole.CO_FOUNDER,
    NormalizedRole.OWNER,
    NormalizedRole.CEO,
}

MARKETING_DM_ROLES = {
    NormalizedRole.CMO,
    NormalizedRole.VP_MARKETING,
    NormalizedRole.HEAD_OF_MARKETING,
    NormalizedRole.MARKETING_DIRECTOR,
    NormalizedRole.HEAD_OF_GROWTH,
    NormalizedRole.HEAD_OF_DIGITAL,
}

QUALIFYING_ROLES = FOUNDER_ROLES | MARKETING_DM_ROLES


class CompanyType(str, Enum):
    UKRAINIAN_FOUNDED_US_BUSINESS = "ukrainian_founded_us_business"
    US_BUSINESS_WITH_UKRAINE_CONNECTED_MARKETER = "us_business_with_ukraine_connected_marketer"
    BOTH = "both"
    UNKNOWN = "unknown"


class USPresenceStatus(str, Enum):
    VERIFIED_US = "verified_us"
    PROBABLE_US = "probable_us"
    NOT_US = "not_us"
    UNKNOWN = "unknown"


class UkraineConnectionStatus(str, Enum):
    VERIFIED = "verified"
    PROBABLE = "probable"
    MANUAL_REVIEW = "manual_review"
    UNKNOWN = "unknown"


class UkraineEvidenceType(str, Enum):
    SELF_IDENTIFICATION = "self_identification"
    OFFICIAL_BIOGRAPHY = "official_biography"
    PROFESSIONAL_BIOGRAPHY = "professional_biography"
    FOUNDER_STORY = "founder_story"
    BUSINESS_COMMUNITY_PROFILE = "business_community_profile"
    CONFERENCE_BIO = "conference_bio"
    INTERVIEW = "interview"
    PUBLIC_COMPANY_PROFILE = "public_company_profile"
    OTHER_PUBLIC_PROFESSIONAL_SOURCE = "other_public_professional_source"

    # Non-evidence discovery signals. These must NEVER be used to raise a
    # Ukraine-connection score above the manual_review floor -- they only
    # justify adding a candidate to the discovery queue.
    DISCOVERY_SIGNAL_NAME = "discovery_signal_name"
    DISCOVERY_SIGNAL_EMPLOYER = "discovery_signal_employer"
    DISCOVERY_SIGNAL_LANGUAGE = "discovery_signal_language"


NON_EVIDENCE_TYPES = {
    UkraineEvidenceType.DISCOVERY_SIGNAL_NAME,
    UkraineEvidenceType.DISCOVERY_SIGNAL_EMPLOYER,
    UkraineEvidenceType.DISCOVERY_SIGNAL_LANGUAGE,
}


class MatchStatus(str, Enum):
    VERIFIED = "verified"
    PROBABLE = "probable"
    MANUAL_REVIEW = "manual_review"
    REJECT = "reject"


class PersonSourceType(str, Enum):
    SEED_DIRECTORY = "seed_directory"
    COMMUNITY_SITE = "community_site"
    EVENT_PAGE = "event_page"
    COMPANY_WEBSITE = "company_website"
    SEARCH_ENGINE = "search_engine"
    LINKEDIN = "linkedin"
    OTHER = "other"


class ManualReviewReason(str, Enum):
    IDENTITY_AMBIGUITY = "identity ambiguity"
    UKRAINE_CONNECTION_AMBIGUITY = "Ukraine connection ambiguity"
    COMPANY_AMBIGUITY = "company ambiguity"
    OLD_EMPLOYMENT = "old employment"
    ROLE_UNCLEAR = "role unclear"
    LOCATION_UNCLEAR = "location unclear"
    DUPLICATE_CONFLICT = "duplicate conflict"
    SOCIAL_PROFILE_AMBIGUITY = "social profile ambiguity"


# ---------------------------------------------------------------------------
# Evidence / sourced-field primitives (Stage 20: source tracking)
# ---------------------------------------------------------------------------


class Evidence(BaseModel):
    """A single piece of public evidence backing a claim about a person or
    company. Deliberately keeps only a short fragment, never a full quote.
    """

    source_url: str
    evidence_type: UkraineEvidenceType | str
    quote_fragment: Optional[str] = Field(default=None, max_length=240)
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("quote_fragment")
    @classmethod
    def _truncate_fragment(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 240:
            return v[:237] + "..."
        return v


class FieldValue(BaseModel):
    """A sourced scalar field, e.g. a phone number or a Telegram handle."""

    value: str
    source_url: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    provider: Optional[str] = None  # e.g. "hunter", "apollo", "website_crawl"


class UkraineConnection(BaseModel):
    status: UkraineConnectionStatus = UkraineConnectionStatus.UNKNOWN
    connection_type: Optional[UkraineEvidenceType] = None
    score: int = 0
    evidence: list[Evidence] = Field(default_factory=list)

    def best_evidence(self) -> Optional[Evidence]:
        real = [e for e in self.evidence if e.evidence_type not in NON_EVIDENCE_TYPES]
        if not real:
            return None
        return max(real, key=lambda e: e.confidence)


# ---------------------------------------------------------------------------
# Source tracking (Stage 20 / sources.csv)
# ---------------------------------------------------------------------------


class DiscoverySource(BaseModel):
    source_id: str = Field(default_factory=_new_id)
    source_name: str
    source_url: str
    source_type: str  # business_directory | business_association | community |
    # event_page | search_query | website_crawl | ukraine_company_seed | ...
    discovered_via: Optional[str] = None  # parent source / query that led here
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    pages_classified: list[str] = Field(default_factory=list)  # members/board/etc


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------


class Company(BaseModel):
    company_id: str = Field(default_factory=_new_id)

    company_name: str
    domain: Optional[str] = None
    website: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "USA"
    industry: Optional[str] = None
    employee_estimate: Optional[int] = None

    company_type: CompanyType = CompanyType.UNKNOWN
    company_source: list[str] = Field(default_factory=list)  # source_ids / names

    us_presence_status: USPresenceStatus = USPresenceStatus.UNKNOWN
    us_presence_evidence: list[Evidence] = Field(default_factory=list)

    # Qualification (Stage 16), filled in later in the pipeline.
    icp_score: float = 0.0
    seo_score: float = 0.0
    ppc_score: float = 0.0
    account_score: float = 0.0

    # crawl bookkeeping
    crawled_pages: list[str] = Field(default_factory=list)
    crawl_signals: dict = Field(default_factory=dict)

    discovery_date: date = Field(default_factory=date.today)

    def merge_source(self, source: str) -> None:
        if source and source not in self.company_source:
            self.company_source.append(source)


# ---------------------------------------------------------------------------
# Person
# ---------------------------------------------------------------------------


class Person(BaseModel):
    person_id: str = Field(default_factory=_new_id)

    full_name: str
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    company_id: Optional[str] = None

    original_job_title: Optional[str] = None
    normalized_role: NormalizedRole = NormalizedRole.OTHER

    city: Optional[str] = None
    state: Optional[str] = None

    linkedin: Optional[FieldValue] = None
    telegram: Optional[FieldValue] = None
    instagram: Optional[FieldValue] = None
    facebook: Optional[FieldValue] = None
    email: Optional[FieldValue] = None
    phone: Optional[FieldValue] = None

    person_source_urls: list[str] = Field(default_factory=list)

    ukraine_connection: UkraineConnection = Field(default_factory=UkraineConnection)

    us_role_status: USPresenceStatus = USPresenceStatus.UNKNOWN

    person_confidence: float = 0.0  # PersonMatcher output (identity confidence)
    manual_review_required: bool = False
    manual_review_reasons: list[ManualReviewReason] = Field(default_factory=list)

    discovered_via: Optional[PersonSourceType] = None
    discovery_date: date = Field(default_factory=date.today)

    def add_source_url(self, url: Optional[str]) -> None:
        if url and url not in self.person_source_urls:
            self.person_source_urls.append(url)

    def flag_for_review(self, reason: ManualReviewReason) -> None:
        self.manual_review_required = True
        if reason not in self.manual_review_reasons:
            self.manual_review_reasons.append(reason)


# ---------------------------------------------------------------------------
# Manual review row
# ---------------------------------------------------------------------------


class ManualReviewRecord(BaseModel):
    person: Optional[str] = None
    company: Optional[str] = None
    candidate_url: Optional[str] = None
    reason: str
    person_confidence: float = 0.0
    ukraine_connection_score: int = 0
    conflicting_evidence: Optional[str] = None
    source_urls: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Discovery log event (discovery_log.jsonl)
# ---------------------------------------------------------------------------


class DiscoveryLogEvent(BaseModel):
    event_id: str = Field(default_factory=_new_id)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stage: str
    event_type: str
    entity_type: Optional[str] = None  # company | person | source
    entity_id: Optional[str] = None
    details: dict = Field(default_factory=dict)
