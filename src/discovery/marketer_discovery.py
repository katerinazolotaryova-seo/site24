"""Marketing decision-maker discovery.

Covers three related but distinct pipelines:
  * Stage 8  MarketingDMDiscovery      -- company -> its CMO/Head of
                                          Marketing/etc.
  * Stage 9  PersonToCompanyDiscovery  -- Ukraine-connected marketers/
                                          founders -> their current US
                                          company (the person -> company
                                          direction of Pipeline B).
  * Stage 10 UkraineCompanyDiscovery   -- known Ukrainian-ecosystem
                                          companies used only as a
                                          *discovery signal* to find
                                          alumni now in US marketing/
                                          growth leadership -- never as
                                          proof of nationality.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from providers.search_provider import SearchProvider
from src.crawling.page_fetcher import PageFetcher
from src.crawling.website_crawler import CrawlResult, WebsiteCrawler
from src.discovery.extraction_utils import extract_company_candidate, extract_person_candidates
from src.logging_setup import get_logger
from src.models import MARKETING_DM_ROLES, Evidence, NormalizedRole, UkraineEvidenceType
from src.processing.role_classifier import RoleClassifier
from src.verification.ukraine_connection import extract_evidence

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Stage 8: company -> marketing decision maker
# ---------------------------------------------------------------------------


def build_marketing_dm_queries(company_name: str) -> list[str]:
    return [
        f'"{company_name}" CMO',
        f'"{company_name}" "Head of Marketing"',
        f'"{company_name}" "Marketing Director"',
        f'"{company_name}" "VP Marketing"',
        f'"{company_name}" "Head of Growth"',
        f'"{company_name}" "Head of Digital"',
    ]


@dataclass
class MarketingDMCandidate:
    full_name: str
    job_title: str | None
    normalized_role: NormalizedRole
    source_url: str
    linkedin: str | None = None


@dataclass
class MarketingDMDiscoveryResult:
    candidates: list[MarketingDMCandidate] = field(default_factory=list)
    company_crawl: CrawlResult | None = None


class MarketingDMDiscovery:
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

    async def discover(self, company_name: str, company_website: str | None) -> MarketingDMDiscoveryResult:
        result = MarketingDMDiscoveryResult()
        seen_names: set[str] = set()

        for query in build_marketing_dm_queries(company_name):
            for hit in await self.provider.search(query):
                fetched = await self.fetcher.fetch(hit.url)
                if fetched is None:
                    continue
                _, data = fetched
                self._collect(data, hit.url, seen_names, result)

        if company_website:
            crawl = await self.website_crawler.crawl(company_website)
            result.company_crawl = crawl
            for page in crawl.pages:
                self._collect(page.data, page.url, seen_names, result)

        log.info("marketing_dm_discovery_complete", company=company_name, found=len(result.candidates))
        return result

    def _collect(self, data, source_url: str, seen_names: set[str], result: MarketingDMDiscoveryResult) -> None:
        for candidate in extract_person_candidates(data, source_url):
            role = self.role_classifier.classify(candidate.get("job_title"))
            if role not in MARKETING_DM_ROLES:
                continue
            key = candidate["full_name"].strip().lower()
            if key in seen_names:
                continue
            seen_names.add(key)
            linkedin = next((link for link in candidate.get("profile_links", []) if "linkedin.com" in link), None)
            result.candidates.append(
                MarketingDMCandidate(
                    full_name=candidate["full_name"],
                    job_title=candidate.get("job_title"),
                    normalized_role=role,
                    source_url=source_url,
                    linkedin=linkedin,
                )
            )


# ---------------------------------------------------------------------------
# Stage 9: person -> company (Ukraine-connected marketers/founders search)
# ---------------------------------------------------------------------------

PERSON_TO_COMPANY_QUERY_TEMPLATES = [
    '"Ukrainian" CMO USA',
    '"Ukrainian" "Head of Marketing" USA',
    '"Ukrainian" "Marketing Director" USA',
    '"Ukrainian" "Head of Growth" USA',
    '"Ukrainian" "Head of Digital" USA',
    '"from Ukraine" CMO',
    '"from Ukraine" "Head of Marketing"',
    '"from Ukraine" "Marketing Director"',
    '"from Ukraine" "Head of Growth"',
    'site:linkedin.com/in "Ukraine" CMO "United States"',
    'site:linkedin.com/in "Ukraine" "Head of Marketing" "United States"',
]


@dataclass
class PersonToCompanyCandidate:
    full_name: str
    job_title: str | None
    normalized_role: NormalizedRole
    current_company_guess: str | None
    source_url: str
    linkedin: str | None
    # Evidence collected from the *fetched page itself*, never the search
    # snippet -- satisfies "наличие слова Ukraine в сниппете не считать
    # подтверждением".
    ukraine_evidence: list[Evidence] = field(default_factory=list)


@dataclass
class PersonToCompanyDiscoveryResult:
    candidates: list[PersonToCompanyCandidate] = field(default_factory=list)


class PersonToCompanyDiscovery:
    def __init__(self, provider: SearchProvider, fetcher: PageFetcher, role_classifier: RoleClassifier | None = None):
        self.provider = provider
        self.fetcher = fetcher
        self.role_classifier = role_classifier or RoleClassifier()

    async def discover(self, max_queries: int | None = None) -> PersonToCompanyDiscoveryResult:
        result = PersonToCompanyDiscoveryResult()
        templates = PERSON_TO_COMPANY_QUERY_TEMPLATES[:max_queries] if max_queries else PERSON_TO_COMPANY_QUERY_TEMPLATES

        for query in templates:
            for hit in await self.provider.search(query):
                fetched = await self.fetcher.fetch(hit.url)
                if fetched is None:
                    continue
                _, data = fetched
                company_guess = extract_company_candidate(data, hit.url)
                for candidate in extract_person_candidates(data, hit.url):
                    role = self.role_classifier.classify(candidate.get("job_title"))
                    if role not in MARKETING_DM_ROLES and role.value not in {"founder", "co_founder", "owner", "ceo"}:
                        continue
                    evidence = extract_evidence(data.text_snippet, hit.url, candidate["full_name"])
                    linkedin = next(
                        (link for link in candidate.get("profile_links", []) if "linkedin.com" in link), None
                    )
                    result.candidates.append(
                        PersonToCompanyCandidate(
                            full_name=candidate["full_name"],
                            job_title=candidate.get("job_title"),
                            normalized_role=role,
                            current_company_guess=company_guess["company_name"] if company_guess else None,
                            source_url=hit.url,
                            linkedin=linkedin,
                            ukraine_evidence=evidence,
                        )
                    )

        log.info("person_to_company_discovery_complete", candidates=len(result.candidates))
        return result


# ---------------------------------------------------------------------------
# Stage 10: known Ukrainian-ecosystem companies as a discovery signal only
# ---------------------------------------------------------------------------


def build_ukraine_company_alumni_queries(ukraine_company: str) -> list[str]:
    return [
        f'"{ukraine_company}" alumni "United States"',
        f'former "{ukraine_company}" "CMO"',
        f'former "{ukraine_company}" "Head of Marketing"',
        f'"{ukraine_company}" "Head of Growth" "United States"',
        f'ex-"{ukraine_company}" marketing "United States"',
    ]


@dataclass
class UkraineCompanyAlumniCandidate:
    full_name: str
    job_title: str | None
    normalized_role: NormalizedRole
    former_ukraine_linked_company: str
    source_url: str
    linkedin: str | None = None
    # Working at a UA-linked company is a DISCOVERY SIGNAL ONLY -- see
    # NON_EVIDENCE_TYPES. It must never be scored as Ukraine-connection
    # evidence on its own.
    discovery_signal_evidence: Evidence | None = None


@dataclass
class UkraineCompanyDiscoveryResult:
    candidates: list[UkraineCompanyAlumniCandidate] = field(default_factory=list)


class UkraineCompanyDiscovery:
    def __init__(self, provider: SearchProvider, fetcher: PageFetcher, role_classifier: RoleClassifier | None = None):
        self.provider = provider
        self.fetcher = fetcher
        self.role_classifier = role_classifier or RoleClassifier()

    async def discover(self, ukraine_companies: list[str]) -> UkraineCompanyDiscoveryResult:
        result = UkraineCompanyDiscoveryResult()
        for ua_company in ukraine_companies:
            for query in build_ukraine_company_alumni_queries(ua_company):
                for hit in await self.provider.search(query):
                    fetched = await self.fetcher.fetch(hit.url)
                    if fetched is None:
                        continue
                    _, data = fetched
                    for candidate in extract_person_candidates(data, hit.url):
                        role = self.role_classifier.classify(candidate.get("job_title"))
                        if role not in MARKETING_DM_ROLES:
                            continue
                        linkedin = next(
                            (link for link in candidate.get("profile_links", []) if "linkedin.com" in link), None
                        )
                        result.candidates.append(
                            UkraineCompanyAlumniCandidate(
                                full_name=candidate["full_name"],
                                job_title=candidate.get("job_title"),
                                normalized_role=role,
                                former_ukraine_linked_company=ua_company,
                                source_url=hit.url,
                                linkedin=linkedin,
                                discovery_signal_evidence=Evidence(
                                    source_url=hit.url,
                                    evidence_type=UkraineEvidenceType.DISCOVERY_SIGNAL_EMPLOYER,
                                    quote_fragment=f"possible alumni of {ua_company}",
                                    confidence=0.0,
                                ),
                            )
                        )
        log.info("ukraine_company_discovery_complete", candidates=len(result.candidates))
        return result
