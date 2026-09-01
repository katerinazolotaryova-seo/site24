"""Provider-independent SEO data interface.

Per brief §23, no pipeline/business logic should depend on a specific
vendor's SDK or response shape. Every module that needs organic traffic,
keywords, SERP, competitors, or backlink data depends on `SEODataProvider`,
never on `DataForSEODataProvider` (or a future Ahrefs/Semrush one) directly.

Every method returns a `RawProviderResponse` — the verbatim payload plus
enough metadata (endpoint name, request params, estimated cost) for the
caller to persist it to `seo_metrics_raw` before any normalization touches
it (plan §24 / §1 risk #12: raw storage is not optional). Normalizing that
payload into the typed `domain_metrics` / `keywords` / etc. tables is the
caller's job, not the provider's — this keeps provider adapters thin and
keeps normalization logic (which encodes business decisions like "what
counts as branded") provider-independent.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class RawProviderResponse:
    """A verbatim provider API response, ready to persist to `seo_metrics_raw`."""

    provider: str
    endpoint: str
    request_params: dict[str, Any]
    raw_response: Any
    estimated_cost_usd: float
    fetched_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class SEODataProvider(ABC):
    """Abstraction over a paid SEO data vendor (DataForSEO, Ahrefs, Semrush, ...).

    Method set matches brief §23 exactly. `get_backlinks` and
    `get_referring_domains` are part of the interface from day one (so
    callers can be written against the full contract now) even though the
    MVP's DataForSEO implementation defers actually calling them to Phase 5
    (see `DataForSEODataProvider`).
    """

    @abstractmethod
    def get_domain_metrics(
        self, domain: str, *, country: str, language: str
    ) -> RawProviderResponse:
        """Organic traffic/keywords/top3/10/20/100 + traffic value for `domain`."""

    @abstractmethod
    def get_organic_keywords(
        self, domain: str, *, country: str, language: str, limit: int = 500
    ) -> RawProviderResponse:
        """Keywords `domain` ranks for, up to `limit` rows."""

    @abstractmethod
    def get_top_pages(
        self, domain: str, *, country: str, language: str, limit: int = 100
    ) -> RawProviderResponse:
        """`domain`'s top pages by estimated organic traffic."""

    @abstractmethod
    def get_competitors(
        self, domain: str, *, country: str, language: str, limit: int = 10
    ) -> RawProviderResponse:
        """Domains the provider considers organic-search competitors of `domain`."""

    @abstractmethod
    def get_backlinks(self, domain: str, *, limit: int = 100) -> RawProviderResponse:
        """`domain`'s backlinks. Not called by the MVP — see Phase 5 (Backlink Profile Analyzer)."""

    @abstractmethod
    def get_referring_domains(self, domain: str, *, limit: int = 100) -> RawProviderResponse:
        """Domains linking to `domain`. Not called by the MVP — see Phase 5."""

    @abstractmethod
    def get_keyword_metrics(
        self, keywords: list[str], *, country: str, language: str
    ) -> RawProviderResponse:
        """Search volume/CPC/competition for an explicit list of keywords."""

    @abstractmethod
    def get_serp(
        self, keyword: str, *, country: str, language: str, depth: int = 10
    ) -> RawProviderResponse:
        """Live SERP for `keyword`, at least `depth` organic results."""
