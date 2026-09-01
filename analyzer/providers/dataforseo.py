"""DataForSEO implementation of `SEODataProvider`.

Endpoint paths/payload shapes below follow DataForSEO's v3 "live" endpoint
convention (POST a list-of-tasks body, Basic Auth with login/password,
response wrapped in `{"tasks": [{"result": [...]}]}`) as of when this was
written. **Verify these paths and response shapes against DataForSEO's
current API docs before pointing this at a real account** — vendor APIs
change, and this module has not been exercised against a live account (see
tests/test_dataforseo_provider.py, which validates it against recorded
fixture responses instead).

`get_backlinks` / `get_referring_domains` intentionally raise
`NotImplementedError` for now — Backlink Profile Analyzer is Phase 5 (plan
§9); the methods exist so callers can already code against the full
`SEODataProvider` interface.
"""

from __future__ import annotations

from typing import Any

import httpx

from analyzer.budget.estimator import CostEstimator, PlannedCall
from analyzer.providers.base import RawProviderResponse, SEODataProvider

PROVIDER_NAME = "dataforseo"


class DataForSEODataProvider(SEODataProvider):
    def __init__(
        self,
        login: str,
        password: str,
        base_url: str = "https://api.dataforseo.com",
        cost_estimator: CostEstimator | None = None,
        client: httpx.Client | None = None,
    ):
        self._cost_estimator = cost_estimator or CostEstimator()
        self._client = client or httpx.Client(
            base_url=base_url,
            auth=(login, password),
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )

    def close(self) -> None:
        self._client.close()

    # -- internal helpers -------------------------------------------------

    def _post(
        self, path: str, task: dict[str, Any], *, endpoint_key: str, row_count: int
    ) -> RawProviderResponse:
        response = self._client.post(path, json=[task])
        response.raise_for_status()
        payload = response.json()
        estimated_cost = self._cost_estimator.estimate_call(
            PlannedCall(endpoint=endpoint_key, row_count=row_count)
        )
        return RawProviderResponse(
            provider=PROVIDER_NAME,
            endpoint=endpoint_key,
            request_params=task,
            raw_response=payload,
            estimated_cost_usd=estimated_cost,
        )

    # -- SEODataProvider ----------------------------------------------------

    def get_domain_metrics(self, domain: str, *, country: str, language: str) -> RawProviderResponse:
        task = {"target": domain, "location_code": country, "language_code": language}
        return self._post(
            "/v3/dataforseo_labs/google/domain_rank_overview/live",
            task,
            endpoint_key="domain_rank_overview",
            row_count=1,
        )

    def get_organic_keywords(
        self, domain: str, *, country: str, language: str, limit: int = 500
    ) -> RawProviderResponse:
        task = {"target": domain, "location_code": country, "language_code": language, "limit": limit}
        return self._post(
            "/v3/dataforseo_labs/google/ranked_keywords/live",
            task,
            endpoint_key="ranked_keywords",
            row_count=limit,
        )

    def get_top_pages(
        self, domain: str, *, country: str, language: str, limit: int = 100
    ) -> RawProviderResponse:
        task = {"target": domain, "location_code": country, "language_code": language, "limit": limit}
        return self._post(
            "/v3/dataforseo_labs/google/relevant_pages/live",
            task,
            endpoint_key="relevant_pages",
            row_count=limit,
        )

    def get_competitors(
        self, domain: str, *, country: str, language: str, limit: int = 10
    ) -> RawProviderResponse:
        task = {"target": domain, "location_code": country, "language_code": language, "limit": limit}
        return self._post(
            "/v3/dataforseo_labs/google/competitors_domain/live",
            task,
            endpoint_key="competitors_domain",
            row_count=1,
        )

    def get_backlinks(self, domain: str, *, limit: int = 100) -> RawProviderResponse:
        raise NotImplementedError(
            "Backlink Profile Analyzer is Phase 5 (see docs plan §9) — "
            "get_backlinks is not wired up yet."
        )

    def get_referring_domains(self, domain: str, *, limit: int = 100) -> RawProviderResponse:
        raise NotImplementedError(
            "Backlink Profile Analyzer is Phase 5 (see docs plan §9) — "
            "get_referring_domains is not wired up yet."
        )

    def get_keyword_metrics(
        self, keywords: list[str], *, country: str, language: str
    ) -> RawProviderResponse:
        task = {"keywords": keywords, "location_code": country, "language_code": language}
        return self._post(
            "/v3/keywords_data/google_ads/search_volume/live",
            task,
            endpoint_key="search_volume",
            row_count=len(keywords),
        )

    def get_serp(
        self, keyword: str, *, country: str, language: str, depth: int = 10
    ) -> RawProviderResponse:
        task = {"keyword": keyword, "location_code": country, "language_code": language, "depth": depth}
        return self._post(
            "/v3/serp/google/organic/live/advanced",
            task,
            endpoint_key="serp_organic_live_advanced",
            row_count=1,
        )
