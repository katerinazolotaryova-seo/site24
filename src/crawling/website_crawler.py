"""WebsiteCrawler (Stage 13): targeted, polite, cached crawl of a single
domain's public pages -- never a full-site crawl.

Only visits the configured `paths` (default: /, /about, /about-us, /team,
/leadership, /management, /contact, /contacts, /company, /blog, /authors,
/press, /media, /careers) plus any same-domain links discovered on those
pages that also classify as "person-bearing" (page_classifier), up to
`max_pages_per_domain`.

Implements: rate limiting (per-domain concurrency + global semaphore),
retry/backoff (tenacity via `provider_retry`), on-disk response caching,
and a dry-run mode (returns nothing, does not touch the network).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from urllib.parse import urljoin, urlparse

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.cache import DiskCache
from src.crawling.page_classifier import classify_path, is_person_bearing
from src.crawling.structured_data_parser import ExtractedPageData, parse_page
from src.logging_setup import get_logger

log = get_logger(__name__)


class FetchError(Exception):
    pass


@dataclass
class CrawledPage:
    url: str
    status_code: int
    category: str
    data: ExtractedPageData


@dataclass
class CrawlResult:
    domain: str
    pages: list[CrawledPage] = field(default_factory=list)

    def merged_emails(self) -> set[str]:
        out: set[str] = set()
        for p in self.pages:
            out |= p.data.emails
        return out

    def merged_phones(self) -> set[str]:
        out: set[str] = set()
        for p in self.pages:
            out |= p.data.phones
        return out

    def merged_social(self) -> dict[str, set[str]]:
        out: dict[str, set[str]] = {}
        for p in self.pages:
            for platform, links in p.data.social_links.items():
                out.setdefault(platform, set()).update(links)
        return out


class WebsiteCrawler:
    def __init__(
        self,
        paths: list[str] | None = None,
        max_pages_per_domain: int = 50,
        timeout: float = 15.0,
        concurrency: int = 10,
        per_domain_concurrency: int = 2,
        user_agent: str = "UkraineUSLeadsBot/1.0",
        cache: DiskCache | None = None,
        dry_run: bool = True,
        max_links_per_page: int = 40,
    ):
        self.paths = paths or [
            "/", "/about", "/about-us", "/team", "/leadership", "/management",
            "/contact", "/contacts", "/company", "/blog", "/authors", "/press",
            "/media", "/careers",
        ]
        self.max_pages_per_domain = max_pages_per_domain
        self.timeout = timeout
        self.global_semaphore = asyncio.Semaphore(concurrency)
        self.per_domain_concurrency = per_domain_concurrency
        self.user_agent = user_agent
        self.cache = cache
        self.dry_run = dry_run
        self.max_links_per_page = max_links_per_page
        self._domain_locks: dict[str, asyncio.Semaphore] = {}

    def _domain_lock(self, domain: str) -> asyncio.Semaphore:
        if domain not in self._domain_locks:
            self._domain_locks[domain] = asyncio.Semaphore(self.per_domain_concurrency)
        return self._domain_locks[domain]

    async def crawl(self, base_url: str) -> CrawlResult:
        if not base_url:
            return CrawlResult(domain="")
        parsed = urlparse(base_url if "://" in base_url else f"https://{base_url}")
        domain = parsed.netloc or parsed.path
        result = CrawlResult(domain=domain)

        if self.dry_run:
            log.debug("crawl_skipped_dry_run", domain=domain)
            return result

        root = f"{parsed.scheme or 'https'}://{domain}"
        seen: set[str] = set()
        queue: list[str] = []
        # If the caller handed us a specific path (e.g. a seed source
        # curated as "https://org.example/list-of-members/" rather than
        # just the bare domain), that's almost certainly the single most
        # relevant page on the site -- fetch it first, in addition to (not
        # instead of) the generic community/company paths below.
        if parsed.path and parsed.path not in ("", "/"):
            queue.append(urljoin(root, parsed.path))
        queue.extend(urljoin(root + "/", p.lstrip("/")) for p in self.paths)

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
        ) as client:
            idx = 0
            while idx < len(queue) and len(result.pages) < self.max_pages_per_domain:
                url = queue[idx]
                idx += 1
                if url in seen:
                    continue
                seen.add(url)

                page = await self._fetch_and_parse(client, domain, url)
                if page is None:
                    continue
                result.pages.append(page)

                # Follow same-domain links from person-bearing pages only,
                # to stay within the "targeted crawl" contract.
                if is_person_bearing(page.category):
                    for link in self._extract_links(page, root):
                        if link not in seen and len(queue) < self.max_pages_per_domain * 3:
                            queue.append(link)

        return result

    def _extract_links(self, page: CrawledPage, root: str) -> list[str]:
        """Same-section same-domain links found on a person-bearing page --
        e.g. a /members listing page linking to its own
        /members/<company-slug>/ detail pages. Deliberately scoped to the
        *same first path segment* as the page we found them on (never an
        offsite link, and never a jump to an unrelated site section) so
        this stays a targeted crawl, not a full-site crawl. Capped per
        page so one huge listing can't alone exhaust the domain's page
        budget.
        """
        section = PurePosixPath(urlparse(page.url).path).parts[:2]  # e.g. ('/', 'members')
        out = []
        for link in sorted(page.data.internal_links):
            link_section = PurePosixPath(urlparse(link).path).parts[:2]
            if link_section == section and link != page.url:
                out.append(link)
        return out[: self.max_links_per_page]

    async def _fetch_and_parse(self, client: httpx.AsyncClient, domain: str, url: str) -> CrawledPage | None:
        cache_key = f"crawl::{url}"
        if self.cache is not None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                category = classify_path(urlparse(url).path)
                return CrawledPage(
                    url=url, status_code=cached.get("status_code", 0), category=category.value,
                    data=parse_page(cached.get("html", ""), url),
                )

        async with self.global_semaphore, self._domain_lock(domain):
            try:
                html, status = await self._fetch(client, url)
            except FetchError as exc:
                log.info("crawl_fetch_failed", url=url, error=str(exc))
                return None

        if self.cache is not None:
            self.cache.set(cache_key, {"html": html, "status_code": status})

        if status >= 400 or not html:
            return None

        category = classify_path(urlparse(url).path)
        return CrawledPage(url=url, status_code=status, category=category.value, data=parse_page(html, url))

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(FetchError),
    )
    async def _fetch(self, client: httpx.AsyncClient, url: str) -> tuple[str, int]:
        try:
            resp = await client.get(url)
        except httpx.HTTPError as exc:
            raise FetchError(str(exc)) from exc
        if resp.status_code >= 500 or resp.status_code == 429:
            raise FetchError(f"status {resp.status_code}")
        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return "", resp.status_code
        return resp.text, resp.status_code
