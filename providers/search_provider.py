"""Generic web-search provider abstraction.

`SearchDiscoveryEngine` (src/discovery/web_discovery.py and friends) only
depends on `SearchProvider.search(query) -> list[SearchResult]`. This module
supplies:

  * `SearchResult` -- normalized hit (title, url, snippet)
  * `NullSearchProvider` -- always returns [] (used when no backend is
    configured; keeps the pipeline runnable offline / in dry-run)
  * `HttpSearchProvider` -- a thin adapter over pluggable HTTP JSON search
    APIs (SerpApi, Google Programmable Search / CSE, Bing Web Search).
    Only one backend needs to be configured via .env; add more backends by
    extending `_BACKEND_BUILDERS` below.

A snippet mentioning "Ukraine" is NEVER treated as evidence by itself
(Stage 9/11 requirement) -- this module only returns raw search hits; all
evidence classification happens in verification/ukraine_connection.py after
the linked page has actually been fetched and read.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx

from providers.base import BaseProvider, ProviderError, provider_retry
from src.cache import DiskCache
from src.logging_setup import get_logger

log = get_logger(__name__)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    query: str


class SearchProvider(BaseProvider):
    name = "search"

    def __init__(
        self,
        backend: str = "none",
        api_key: Optional[str] = None,
        cse_id: Optional[str] = None,
        rps: float = 1.0,
        dry_run: bool = True,
        cache: Optional[DiskCache] = None,
        max_results: int = 10,
    ):
        enabled = backend != "none" and bool(api_key)
        super().__init__(enabled=enabled, dry_run=dry_run, rps=rps, credit_limit=0)
        self.backend = backend
        self.api_key = api_key
        self.cse_id = cse_id
        self.cache = cache
        self.max_results = max_results

    async def search(self, query: str) -> list[SearchResult]:
        cache_key = f"search::{self.backend}::{query}"
        if self.cache is not None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return [SearchResult(**r) for r in cached]

        if not self.is_usable():
            log.debug("search_skipped_dry_run_or_disabled", query=query, backend=self.backend)
            return []

        await self.limiter.acquire()
        try:
            results = await self._dispatch(query)
        except ProviderError as exc:
            log.warning("search_provider_failed", query=query, error=str(exc))
            return []

        if self.cache is not None:
            self.cache.set(cache_key, [r.__dict__ for r in results])
        return results

    async def _dispatch(self, query: str) -> list[SearchResult]:
        if self.backend == "serpapi":
            return await self._search_serpapi(query)
        if self.backend == "google_cse":
            return await self._search_google_cse(query)
        if self.backend == "bing":
            return await self._search_bing(query)
        return []

    @provider_retry()
    async def _search_serpapi(self, query: str) -> list[SearchResult]:
        params = {"q": query, "api_key": self.api_key, "num": self.max_results, "engine": "google"}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get("https://serpapi.com/search", params=params)
        except httpx.HTTPError as exc:
            raise ProviderError(str(exc)) from exc
        if resp.status_code >= 500 or resp.status_code == 429:
            raise ProviderError(f"serpapi status {resp.status_code}")
        if resp.status_code >= 400:
            log.warning("serpapi_client_error", status=resp.status_code, query=query)
            return []
        payload = resp.json()
        out = []
        for item in payload.get("organic_results", [])[: self.max_results]:
            out.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    query=query,
                )
            )
        return out

    @provider_retry()
    async def _search_google_cse(self, query: str) -> list[SearchResult]:
        params = {"q": query, "key": self.api_key, "cx": self.cse_id, "num": min(self.max_results, 10)}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get("https://www.googleapis.com/customsearch/v1", params=params)
        except httpx.HTTPError as exc:
            raise ProviderError(str(exc)) from exc
        if resp.status_code >= 500 or resp.status_code == 429:
            raise ProviderError(f"google_cse status {resp.status_code}")
        if resp.status_code >= 400:
            log.warning("google_cse_client_error", status=resp.status_code, query=query)
            return []
        payload = resp.json()
        out = []
        for item in payload.get("items", [])[: self.max_results]:
            out.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    query=query,
                )
            )
        return out

    @provider_retry()
    async def _search_bing(self, query: str) -> list[SearchResult]:
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {"q": query, "count": self.max_results}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://api.bing.microsoft.com/v7.0/search", params=params, headers=headers
                )
        except httpx.HTTPError as exc:
            raise ProviderError(str(exc)) from exc
        if resp.status_code >= 500 or resp.status_code == 429:
            raise ProviderError(f"bing status {resp.status_code}")
        if resp.status_code >= 400:
            log.warning("bing_client_error", status=resp.status_code, query=query)
            return []
        payload = resp.json()
        out = []
        for item in payload.get("webPages", {}).get("value", [])[: self.max_results]:
            out.append(
                SearchResult(
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    query=query,
                )
            )
        return out


class NullSearchProvider(SearchProvider):
    """Explicit no-op provider, useful in tests."""

    def __init__(self):
        super().__init__(backend="none", dry_run=True)
