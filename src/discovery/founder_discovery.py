"""FounderDiscovery (Stage 7): given a company, finds its
Founder/Co-founder/Owner/CEO via targeted search queries and the company's
own /about, /about-us, /team, /leadership, /company, /management pages.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from providers.search_provider import SearchProvider
from src.crawling.page_fetcher import PageFetcher
from src.crawling.website_crawler import CrawlResult, WebsiteCrawler
from src.discovery.extraction_utils import extract_person_candidates
from src.logging_setup import get_logger
from src.models import FOUNDER_ROLES, NormalizedRole
from src.processing.role_classifier import RoleClassifier

log = get_logger(__name__)


def build_founder_queries(company_name: str) -> list[str]:
    return [
        f'"{company_name}" founder',
        f'"{company_name}" co-founder',
        f'"{company_name}" owner',
        f'"{company_name}" CEO',
        f'site:linkedin.com/in "{company_name}" founder',
        f'site:linkedin.com/in "{company_name}" CEO',
    ]


@dataclass
class FounderCandidate:
    full_name: str
    job_title: str | None
    normalized_role: NormalizedRole
    source_url: str
    linkedin: str | None = None


@dataclass
class FounderDiscoveryResult:
    candidates: list[FounderCandidate] = field(default_factory=list)
    company_crawl: CrawlResult | None = None


class FounderDiscovery:
    def __init__(
        self,
        provider: SearchProvider,
        fetcher: PageFetcher,
        website_crawler: WebsiteCrawler,
        role_classifier: RoleClassifier | None = None,
    ):
        self.provider = provider
        self.fetcher = fetcher
        self.website_crawler = website_crawler
        self.role_classifier = role_classifier or RoleClassifier()

    async def discover(self, company_name: str, company_website: str | None) -> FounderDiscoveryResult:
        result = FounderDiscoveryResult()
        seen_names: set[str] = set()

        for query in build_founder_queries(company_name):
            for hit in await self.provider.search(query):
                fetched = await self.fetcher.fetch(hit.url)
                if fetched is None:
                    continue
                _, data = fetched
                self._collect_founder_candidates(data, hit.url, seen_names, result)

        if company_website:
            crawl = await self.website_crawler.crawl(company_website)
            result.company_crawl = crawl
            for page in crawl.pages:
                self._collect_founder_candidates(page.data, page.url, seen_names, result)

        log.info("founder_discovery_complete", company=company_name, founders_found=len(result.candidates))
        return result

    def _collect_founder_candidates(self, data, source_url: str, seen_names: set[str], result: FounderDiscoveryResult) -> None:
        for candidate in extract_person_candidates(data, source_url):
            role = self.role_classifier.classify(candidate.get("job_title"))
            if role not in FOUNDER_ROLES:
                continue
            key = candidate["full_name"].strip().lower()
            if key in seen_names:
                continue
            seen_names.add(key)
            linkedin = next((link for link in candidate.get("profile_links", []) if "linkedin.com" in link), None)
            result.candidates.append(
                FounderCandidate(
                    full_name=candidate["full_name"],
                    job_title=candidate.get("job_title"),
                    normalized_role=role,
                    source_url=source_url,
                    linkedin=linkedin,
                )
            )
