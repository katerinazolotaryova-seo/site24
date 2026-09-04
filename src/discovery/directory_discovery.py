"""DirectoryDiscovery (Stage 1): extracts company_name, website,
person_name, job_title, city, state, industry, source_url from Ukrainian
business directories / associations / communities in the seed file (and
anything Stage 5 community discovery queues up afterwards).

IMPORTANT (per spec): being listed on an organization's member/board/
directory page is NOT itself treated as confirmed evidence of that
person's Ukraine connection -- it is only enough to create the Person
record and a `business_community_profile`-type evidence candidate, which
verification/ukraine_connection.py still scores on its own merits (a
generic membership listing with no biographical text about the person
scores low / manual_review, not verified).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath
from urllib.parse import urlparse

from src.cache import DiskCache
from src.crawling.page_classifier import PageCategory, is_person_bearing
from src.crawling.website_crawler import WebsiteCrawler
from src.discovery.extraction_utils import (
    extract_company_candidate,
    extract_company_candidates_from_headings,
    extract_person_candidates,
)
from src.logging_setup import get_logger
from src.models import DiscoverySource

log = get_logger(__name__)

COMMUNITY_PATHS = [
    "/", "/about", "/members", "/member-directory", "/directory", "/board",
    "/leadership", "/speakers", "/participants", "/sponsors", "/partners",
    "/companies", "/founders", "/events",
]

# Pages that list *many* companies -- extract each one from per-item
# heading patterns, never from a single page-level guess.
LISTING_CATEGORIES = frozenset(
    {
        PageCategory.MEMBERS,
        PageCategory.DIRECTORY,
        PageCategory.SPONSORS,
        PageCategory.PARTNERS,
        PageCategory.FOUNDERS,
        PageCategory.COMPANIES,
    }
)
# Pages that are plausibly *about one specific company* (a dedicated
# company-profile page on the directory site) -- safe to use the
# JSON-LD/page-title single-company guess here.
SINGLE_COMPANY_CATEGORIES = frozenset({PageCategory.COMPANY})


@dataclass
class DirectoryExtractionResult:
    source: DiscoverySource
    people: list[dict] = field(default_factory=list)
    companies: list[dict] = field(default_factory=list)


class DirectoryDiscovery:
    def __init__(
        self,
        max_pages_per_domain: int = 50,
        timeout: float = 15.0,
        concurrency: int = 10,
        per_domain_concurrency: int = 2,
        user_agent: str = "UkraineUSLeadsBot/1.0",
        cache: DiskCache | None = None,
        dry_run: bool = True,
    ):
        self.crawler = WebsiteCrawler(
            paths=COMMUNITY_PATHS,
            max_pages_per_domain=max_pages_per_domain,
            timeout=timeout,
            concurrency=concurrency,
            per_domain_concurrency=per_domain_concurrency,
            user_agent=user_agent,
            cache=cache,
            dry_run=dry_run,
        )

    async def extract_from_source(self, source: DiscoverySource) -> DirectoryExtractionResult:
        result = DirectoryExtractionResult(source=source)
        crawl = await self.crawler.crawl(source.source_url)

        for page in crawl.pages:
            try:
                category = PageCategory(page.category)
            except ValueError:
                category = PageCategory.OTHER

            if is_person_bearing(category):
                people = extract_person_candidates(page.data, page.url)
                for p in people:
                    p["city"] = None
                    p["state"] = None
                    p["industry"] = None
                    p["found_via_source"] = source.source_name
                result.people.extend(people)

            # Only pull "company" candidates from pages that plausibly list
            # *member/portfolio* companies -- not HOME/ABOUT/COMPANY, which
            # on an association's own site almost always describe the
            # association itself (its own JSON-LD Organization block, or a
            # weak page-<title> guess like "About U.S. UCC"), not a target
            # company. Trades a little recall for precision, matching the
            # project's overall bias.
            #
            # A real member-directory site typically has both an *index*
            # page (/members -- no single company to name, many links out)
            # and, one level down, one *detail* page per member
            # (/members/griffith-roofing/ -- an actual single-company page
            # whose own <h1>/<title>/JSON-LD names it). classify_path()
            # can't tell those apart (both contain "members"), so use path
            # depth instead: an index page has <=1 path segment, a detail
            # page has more.
            is_index_page = len(PurePosixPath(urlparse(page.url).path).parts) <= 2  # ('/', 'members')
            if category in LISTING_CATEGORIES and is_index_page:
                # The page-<title> single-company fallback is meaningless
                # on an index page ("Business Members Directory" is not a
                # company), and a global site-wide JSON-LD Organization
                # block that shows up on every page of the association's
                # own site (its own identity, not a member) is exactly
                # what we're trying to exclude here, so we skip the
                # single-candidate helper entirely and only take explicit
                # per-company heading matches.
                for company_candidate in extract_company_candidates_from_headings(page.data, page.url):
                    company_candidate["found_via_source"] = source.source_name
                    result.companies.append(company_candidate)
            elif category in LISTING_CATEGORIES or category in SINGLE_COMPANY_CATEGORIES:
                # A listing *detail* page, or an explicit single-company
                # page -- both plausibly describe exactly one company.
                company_candidate = extract_company_candidate(page.data, page.url)
                if company_candidate:
                    company_candidate["found_via_source"] = source.source_name
                    result.companies.append(company_candidate)

        log.info(
            "directory_source_extracted",
            source=source.source_name,
            people_found=len(result.people),
            companies_found=len(result.companies),
            pages_crawled=len(crawl.pages),
        )
        return result
