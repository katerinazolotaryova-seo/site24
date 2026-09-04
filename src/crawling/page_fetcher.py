"""Single-URL fetcher, distinct from WebsiteCrawler (which does a targeted
multi-page crawl of one *domain*). Discovery modules use this to open one
specific public URL -- a search hit, an event speaker page, a conference
bio -- to read its actual content before treating anything on it as
evidence (never trust a search snippet alone).
"""

from __future__ import annotations

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.cache import DiskCache
from src.crawling.structured_data_parser import ExtractedPageData, parse_page
from src.logging_setup import get_logger

log = get_logger(__name__)


class FetchError(Exception):
    pass


class PageFetcher:
    def __init__(
        self,
        timeout: float = 15.0,
        user_agent: str = "UkraineUSLeadsBot/1.0",
        cache: DiskCache | None = None,
        dry_run: bool = True,
    ):
        self.timeout = timeout
        self.user_agent = user_agent
        self.cache = cache
        self.dry_run = dry_run

    async def fetch(self, url: str) -> tuple[str, ExtractedPageData] | None:
        """Returns (html, parsed_data) or None if unreachable/blocked/dry-run."""
        if not url:
            return None

        cache_key = f"page::{url}"
        if self.cache is not None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                html = cached.get("html", "")
                return html, parse_page(html, url)

        if self.dry_run:
            log.debug("page_fetch_skipped_dry_run", url=url)
            return None

        try:
            html, status = await self._fetch(url)
        except FetchError as exc:
            log.info("page_fetch_failed", url=url, error=str(exc))
            return None

        if self.cache is not None:
            self.cache.set(cache_key, {"html": html, "status_code": status})

        if status >= 400 or not html:
            return None
        return html, parse_page(html, url)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(FetchError),
    )
    async def _fetch(self, url: str) -> tuple[str, int]:
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, headers={"User-Agent": self.user_agent}, follow_redirects=True
            ) as client:
                resp = await client.get(url)
        except httpx.HTTPError as exc:
            raise FetchError(str(exc)) from exc
        if resp.status_code >= 500 or resp.status_code == 429:
            raise FetchError(f"status {resp.status_code}")
        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return "", resp.status_code
        return resp.text, resp.status_code
