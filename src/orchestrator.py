"""Pipeline orchestrator (Stage 21):

    DISCOVER SOURCES
           v
    DISCOVER PEOPLE / COMPANIES
           v
    NORMALIZE
           v
    DEDUPLICATE
           v
    VERIFY UKRAINE CONNECTION
           v
    VERIFY US COMPANY
           v
    CRAWL COMPANY WEBSITE
           v
    IDENTIFY FOUNDER / MARKETING DM
           v
    ACCOUNT QUALIFICATION
           v
    SEO / PPC SCORE
           v
    FILTER LOW-VALUE ACCOUNTS
           v
    CONTACT ENRICHMENT
           v
    CONTACT CONFIDENCE
           v
    MANUAL REVIEW
           v
    EXPORT

Cost discipline: expensive per-person enrichment (Hunter/Apollo calls) only
ever runs after FILTER LOW-VALUE ACCOUNTS, and only for the priority roles
on the surviving companies -- see enrichment/waterfall.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.cache import DiskCache
from src.checkpoint import CheckpointStore
from src.config import AppConfig
from src.crawling.page_fetcher import PageFetcher
from src.crawling.website_crawler import WebsiteCrawler
from src.discovery.directory_discovery import DirectoryDiscovery
from src.discovery.event_discovery import EventDiscoveryModule
from src.discovery.founder_discovery import FounderDiscovery
from src.discovery.marketer_discovery import (
    MarketingDMDiscovery,
    PersonToCompanyDiscovery,
    UkraineCompanyDiscovery,
)
from src.discovery.source_discovery import CommunityDiscovery, load_seed_sources
from src.discovery.web_discovery import SearchDiscoveryEngine
from src.enrichment.waterfall import ContactWaterfall
from src.exporters.csv_exporter import (
    write_companies_csv,
    write_manual_review_csv,
    write_people_csv,
    write_qualified_accounts_csv,
    write_sources_csv,
)
from src.exporters.json_exporter import DiscoveryLogWriter
from src.logging_setup import get_logger
from src.models import (
    Company,
    CompanyType,
    DiscoverySource,
    ManualReviewRecord,
    NormalizedRole,
    Person,
    UkraineConnectionStatus,
)
from src.processing.deduplicator import Deduplicator
from src.processing.normalizer import normalize_company, normalize_domain, normalize_person
from src.processing.role_classifier import RoleClassifier
from src.qualification.account_score import AccountQualificationEngine
from src.qualification.ppc_score import score_ppc_opportunity
from src.qualification.seo_score import score_seo_opportunity
from src.verification.company_matcher import CompanyMatcher
from src.verification.person_matcher import PersonMatcher
from src.verification.ukraine_connection import ScoreThresholds, UkraineConnectionVerifier
from src.verification.us_company import USCompanyVerifier

from providers.apollo import ApolloProvider
from providers.hunter import HunterProvider
from providers.search_provider import SearchProvider

log = get_logger(__name__)


@dataclass
class PipelineState:
    sources: list[DiscoverySource] = field(default_factory=list)
    companies: list[Company] = field(default_factory=list)
    people: list[Person] = field(default_factory=list)
    manual_review: list[ManualReviewRecord] = field(default_factory=list)
    qualified_rows: list[dict] = field(default_factory=list)


class Orchestrator:
    def __init__(self, config: AppConfig):
        self.config = config
        self.cache = DiskCache(config.cache_dir, ttl_hours=config.get("run.cache_ttl_hours", 168))
        self.checkpoints = CheckpointStore(config.checkpoint_dir) if config.get("run.checkpoint_enabled", True) else None
        self.log_writer = DiscoveryLogWriter(config.output_dir / config.get("output.discovery_log_jsonl", "discovery_log.jsonl"))

        self.search_provider = SearchProvider(
            backend=config.search_backend,
            api_key=config.search_api_key,
            cse_id=config.search_cse_id,
            rps=config.search_rps,
            dry_run=config.dry_run,
            cache=self.cache,
            max_results=config.get("discovery.max_results_per_query", 10),
        )
        self.hunter = HunterProvider(
            api_key=config.hunter_api_key,
            enabled=config.hunter_enabled,
            dry_run=config.dry_run,
            credit_limit=config.hunter_credit_limit,
        )
        self.apollo = ApolloProvider(
            api_key=config.apollo_api_key,
            enabled=config.apollo_enabled,
            dry_run=config.dry_run,
            credit_limit=config.apollo_credit_limit,
        )

        self.fetcher = PageFetcher(
            timeout=config.get("crawler.timeout", 15),
            user_agent=config.get("crawler.user_agent", "UkraineUSLeadsBot/1.0"),
            cache=self.cache,
            dry_run=config.dry_run,
        )
        self.website_crawler = WebsiteCrawler(
            paths=config.get("crawler.paths"),
            max_pages_per_domain=config.get("crawler.max_pages_per_domain", 50),
            timeout=config.get("crawler.timeout", 15),
            concurrency=config.get("crawler.concurrency", 10),
            per_domain_concurrency=config.get("crawler.per_domain_concurrency", 2),
            user_agent=config.get("crawler.user_agent", "UkraineUSLeadsBot/1.0"),
            cache=self.cache,
            dry_run=config.dry_run,
        )

        self.role_classifier = RoleClassifier(config)
        self.ukraine_verifier = UkraineConnectionVerifier(
            ScoreThresholds(
                verified=config.get("verification.ukraine_connection.verified_threshold", 85),
                probable=config.get("verification.ukraine_connection.probable_threshold", 65),
                manual_review=config.get("verification.ukraine_connection.manual_review_threshold", 40),
            )
        )
        self.us_verifier = USCompanyVerifier()
        self.company_matcher = CompanyMatcher(
            verified_threshold=config.get("matching.company.verified_threshold", 80),
            probable_threshold=config.get("matching.company.probable_threshold", 60),
            manual_review_threshold=config.get("matching.company.manual_review_threshold", 40),
        )
        self.person_matcher = PersonMatcher(
            verified_threshold=config.get("matching.person.verified_threshold", 80),
            probable_threshold=config.get("matching.person.probable_threshold", 60),
            manual_review_threshold=config.get("matching.person.manual_review_threshold", 40),
        )
        self.deduplicator = Deduplicator(self.company_matcher, self.person_matcher)
        self.qualification_engine = AccountQualificationEngine(
            weights=config.qualification_weights,
            min_account_score=config.get("qualification.min_account_score", 65),
        )
        self.waterfall = ContactWaterfall(
            hunter=self.hunter,
            apollo=self.apollo,
            skip_email_if_confidence_gte=config.get("enrichment.skip_email_if_confidence_gte", 0.90),
            skip_phone_if_confidence_gte=config.get("enrichment.skip_phone_if_confidence_gte", 0.90),
        )

        self.state = PipelineState()

    # ------------------------------------------------------------------
    # Stage: DISCOVER SOURCES
    # ------------------------------------------------------------------

    async def discover_sources(self, seed_path: str | None) -> None:
        sources: list[DiscoverySource] = []
        if seed_path and self.config.get("discovery.seed_sources", True):
            sources.extend(load_seed_sources(seed_path))

        if self.config.get("discovery.communities", True):
            community = CommunityDiscovery(self.search_provider)
            cities = [c["name"] if isinstance(c, dict) else c for c in self.config.cities]
            community_result = await community.discover(cities=cities[:5])
            sources.extend(community_result.new_sources)

        self.state.sources = sources
        for s in sources:
            self.log_writer.log("discover_sources", "source_found", entity_type="source", entity_id=s.source_id, source_name=s.source_name)
        log.info("stage_discover_sources_complete", total_sources=len(sources))

    # ------------------------------------------------------------------
    # ЭТАП 1 only: seed discovery, run standalone (no community/web/event/
    # founder/marketer/person->company discovery, no verification or
    # qualification -- just "read the seed sources, extract what's on
    # them"). Useful for validating/inspecting a seed file in isolation
    # before running the full pipeline.
    # ------------------------------------------------------------------

    async def run_seed_discovery_only(self, seed_path: str) -> PipelineState:
        sources = load_seed_sources(seed_path)
        self.state.sources = sources
        for s in sources:
            self.log_writer.log(
                "seed_discovery", "source_loaded", entity_type="source", entity_id=s.source_id, source_name=s.source_name, source_url=s.source_url
            )

        directory = DirectoryDiscovery(
            max_pages_per_domain=self.config.get("crawler.max_pages_per_domain", 50),
            timeout=self.config.get("crawler.timeout", 15),
            concurrency=self.config.get("crawler.concurrency", 10),
            per_domain_concurrency=self.config.get("crawler.per_domain_concurrency", 2),
            user_agent=self.config.get("crawler.user_agent", "UkraineUSLeadsBot/1.0"),
            cache=self.cache,
            dry_run=self.config.dry_run,
        )

        companies: list[Company] = []
        people: list[Person] = []
        for source in sources:
            extraction = await directory.extract_from_source(source)
            for c in extraction.companies:
                companies.append(self._company_from_candidate(c, source))
            for p in extraction.people:
                people.append(self._person_from_directory_candidate(p, source))
            self.log_writer.log(
                "seed_discovery",
                "source_extracted",
                entity_type="source",
                entity_id=source.source_id,
                source_name=source.source_name,
                companies_found=len(extraction.companies),
                people_found=len(extraction.people),
            )

        self.state.companies = companies
        self.state.people = people
        self.normalize()

        out = self.config.output_dir
        write_sources_csv(self.state.sources, out / self.config.get("output.sources_csv", "sources.csv"))
        write_companies_csv(self.state.companies, out / self.config.get("output.companies_csv", "companies.csv"))
        write_people_csv(self.state.people, out / self.config.get("output.people_csv", "people.csv"))

        log.info(
            "seed_discovery_complete",
            sources=len(self.state.sources),
            companies=len(self.state.companies),
            people=len(self.state.people),
        )
        return self.state

    # ------------------------------------------------------------------
    # Stage: DISCOVER PEOPLE / COMPANIES
    # ------------------------------------------------------------------

    async def discover_people_and_companies(self) -> None:
        companies: list[Company] = []
        people: list[Person] = []

        # Pipeline A leg 1: directories/associations/communities (Stage 1)
        directory = DirectoryDiscovery(
            max_pages_per_domain=self.config.get("crawler.max_pages_per_domain", 50),
            timeout=self.config.get("crawler.timeout", 15),
            concurrency=self.config.get("crawler.concurrency", 10),
            per_domain_concurrency=self.config.get("crawler.per_domain_concurrency", 2),
            user_agent=self.config.get("crawler.user_agent", "UkraineUSLeadsBot/1.0"),
            cache=self.cache,
            dry_run=self.config.dry_run,
        )
        for source in self.state.sources:
            extraction = await directory.extract_from_source(source)
            for c in extraction.companies:
                companies.append(self._company_from_candidate(c, source))
            for p in extraction.people:
                people.append(self._person_from_directory_candidate(p, source))

        # Pipeline A leg 2: general/state/city web discovery (Stages 2-4)
        if self.config.get("discovery.states", True) or self.config.get("discovery.cities", True):
            search_engine = SearchDiscoveryEngine(
                self.search_provider, max_queries_per_stage=self.config.get("discovery.max_queries_per_stage", 200)
            )
            hits = list(await search_engine.discover_general())
            if self.config.get("discovery.states", True):
                hits += await search_engine.discover_states(self.config.states)
            if self.config.get("discovery.cities", True):
                hits += await search_engine.discover_cities(self.config.cities)
            for hit in hits:
                self.log_writer.log("web_discovery", "search_hit", url=hit.url, query=hit.query)

        # Pipeline A leg 3: events (Stage 6)
        if self.config.get("discovery.events", True):
            events = EventDiscoveryModule(self.search_provider, self.fetcher)
            event_result = await events.discover()
            for speaker in event_result.speakers:
                people.append(self._person_from_event_speaker(speaker))

        # Pipeline A leg 4: founder + marketing DM discovery per known company
        founder_disco = FounderDiscovery(self.search_provider, self.fetcher, self.website_crawler, self.role_classifier)
        marketer_disco = MarketingDMDiscovery(self.search_provider, self.fetcher, self.website_crawler, self.role_classifier)
        if self.config.get("discovery.founder_discovery", True) or self.config.get("discovery.marketer_discovery", True):
            for company in list(companies):
                if self.config.get("discovery.founder_discovery", True):
                    f_result = await founder_disco.discover(company.company_name, company.website)
                    for cand in f_result.candidates:
                        people.append(self._person_from_role_candidate(cand, company))
                    if f_result.company_crawl:
                        self._apply_crawl_signals(company, f_result.company_crawl)
                if self.config.get("discovery.marketer_discovery", True):
                    m_result = await marketer_disco.discover(company.company_name, company.website)
                    for cand in m_result.candidates:
                        people.append(self._person_from_role_candidate(cand, company))
                    if m_result.company_crawl:
                        self._apply_crawl_signals(company, m_result.company_crawl)

        # Pipeline B: person -> company (Stage 9) + Ukraine-company alumni (Stage 10)
        if self.config.get("discovery.person_to_company", True):
            p2c = PersonToCompanyDiscovery(self.search_provider, self.fetcher, self.role_classifier)
            p2c_result = await p2c.discover()
            for cand in p2c_result.candidates:
                person, company = self._person_and_company_from_p2c(cand)
                people.append(person)
                if company is not None:
                    companies.append(company)

        if self.config.get("discovery.ukraine_company_seed", True):
            ua_disco = UkraineCompanyDiscovery(self.search_provider, self.fetcher, self.role_classifier)
            ua_result = await ua_disco.discover(self.config.ukraine_companies)
            for cand in ua_result.candidates:
                people.append(self._person_from_ukraine_alumni_candidate(cand))

        self.state.companies = companies
        self.state.people = people
        log.info("stage_discover_people_companies_complete", companies=len(companies), people=len(people))

    # -- candidate -> model conversion helpers -----------------------------

    def _company_from_candidate(self, candidate: dict, source: DiscoverySource) -> Company:
        return Company(
            company_name=candidate["company_name"],
            website=candidate.get("website"),
            domain=normalize_domain(candidate.get("website")),
            company_source=[source.source_name],
        )

    def _person_from_directory_candidate(self, candidate: dict, source: DiscoverySource) -> Person:
        role = self.role_classifier.classify(candidate.get("job_title"))
        person = Person(
            full_name=candidate["full_name"],
            original_job_title=candidate.get("job_title"),
            normalized_role=role,
            city=candidate.get("city"),
            state=candidate.get("state"),
        )
        person.add_source_url(candidate.get("source_url"))
        # Being on an org's page is a discovery signal, not evidence -- see
        # verification/ukraine_connection.py NON_EVIDENCE_TYPES.
        from src.models import Evidence, UkraineEvidenceType

        person.ukraine_connection.evidence.append(
            Evidence(
                source_url=candidate.get("source_url", source.source_url),
                evidence_type=UkraineEvidenceType.DISCOVERY_SIGNAL_NAME,
                quote_fragment=f"listed on {source.source_name}",
                confidence=0.0,
            )
        )
        return person

    def _person_from_event_speaker(self, speaker) -> Person:
        role = self.role_classifier.classify(speaker.job_title)
        person = Person(
            full_name=speaker.full_name,
            original_job_title=speaker.job_title,
            normalized_role=role,
            city=speaker.city,
            state=speaker.state,
        )
        person.add_source_url(speaker.source_url)
        if speaker.linkedin:
            from src.models import FieldValue

            person.linkedin = FieldValue(value=speaker.linkedin, source_url=speaker.source_url, confidence=0.7, provider="event_page")
        if speaker.bio_snippet:
            from src.verification.ukraine_connection import extract_evidence

            person.ukraine_connection.evidence.extend(
                extract_evidence(speaker.bio_snippet, speaker.source_url, speaker.full_name)
            )
        return person

    def _person_from_role_candidate(self, candidate, company: Company) -> Person:
        from src.models import FieldValue

        person = Person(
            full_name=candidate.full_name,
            company_name=company.company_name,
            company_domain=company.domain,
            company_id=company.company_id,
            original_job_title=candidate.job_title,
            normalized_role=candidate.normalized_role,
        )
        person.add_source_url(candidate.source_url)
        if candidate.linkedin:
            person.linkedin = FieldValue(value=candidate.linkedin, source_url=candidate.source_url, confidence=0.7, provider="search")
        return person

    def _person_and_company_from_p2c(self, candidate) -> tuple[Person, Company | None]:
        from src.models import FieldValue

        person = Person(
            full_name=candidate.full_name,
            company_name=candidate.current_company_guess,
            original_job_title=candidate.job_title,
            normalized_role=candidate.normalized_role,
        )
        person.add_source_url(candidate.source_url)
        if candidate.linkedin:
            person.linkedin = FieldValue(value=candidate.linkedin, source_url=candidate.source_url, confidence=0.7, provider="search")
        person.ukraine_connection.evidence.extend(candidate.ukraine_evidence)

        company = None
        if candidate.current_company_guess:
            company = Company(company_name=candidate.current_company_guess, company_source=["person_to_company_discovery"])
            person.company_domain = company.domain
            person.company_id = company.company_id
        return person, company

    def _person_from_ukraine_alumni_candidate(self, candidate) -> Person:
        from src.models import FieldValue

        person = Person(
            full_name=candidate.full_name,
            original_job_title=candidate.job_title,
            normalized_role=candidate.normalized_role,
        )
        person.add_source_url(candidate.source_url)
        if candidate.linkedin:
            person.linkedin = FieldValue(value=candidate.linkedin, source_url=candidate.source_url, confidence=0.7, provider="search")
        if candidate.discovery_signal_evidence:
            person.ukraine_connection.evidence.append(candidate.discovery_signal_evidence)
        return person

    def _apply_crawl_signals(self, company: Company, crawl) -> None:
        for page in crawl.pages:
            if page.url not in company.crawled_pages:
                company.crawled_pages.append(page.url)
        phones = crawl.merged_phones()
        if phones and "phone" not in company.crawl_signals:
            company.crawl_signals["phone"] = sorted(phones)[0]
        signals = self.us_verifier.signals_from_address(company.city, company.state, " ".join(phones) if phones else None)
        if signals.us_corporate_address:
            company.crawl_signals["us_corporate_address"] = True

    # ------------------------------------------------------------------
    # Stage: NORMALIZE
    # ------------------------------------------------------------------

    def normalize(self) -> None:
        self.state.companies = [normalize_company(c) for c in self.state.companies]
        self.state.people = [normalize_person(p) for p in self.state.people]
        log.info("stage_normalize_complete")

    # ------------------------------------------------------------------
    # Stage: DEDUPLICATE
    # ------------------------------------------------------------------

    def deduplicate(self) -> None:
        companies, company_merges, company_conflicts = self.deduplicator.dedupe_companies(self.state.companies)
        people, person_merges, person_conflicts = self.deduplicator.dedupe_people(self.state.people)

        self.state.companies = companies
        self.state.people = people

        for conflict in company_conflicts:
            self.state.manual_review.append(
                ManualReviewRecord(
                    company=conflict["company"],
                    reason="duplicate conflict",
                    conflicting_evidence=f"possible match: {conflict['candidate_match']} (score={conflict['score']})",
                )
            )
        for conflict in person_conflicts:
            self.state.manual_review.append(
                ManualReviewRecord(
                    person=conflict["person"],
                    reason="duplicate conflict",
                    conflicting_evidence=f"possible match: {conflict['candidate_match']} (score={conflict['score']})",
                )
            )

        log.info(
            "stage_deduplicate_complete",
            companies=len(companies),
            people=len(people),
            company_merges=len(company_merges),
            person_merges=len(person_merges),
        )

    # ------------------------------------------------------------------
    # Stage: VERIFY UKRAINE CONNECTION
    # ------------------------------------------------------------------

    def verify_ukraine_connections(self) -> None:
        for person in self.state.people:
            person.ukraine_connection = self.ukraine_verifier.score_evidence(person.ukraine_connection.evidence)
            if person.ukraine_connection.status == UkraineConnectionStatus.MANUAL_REVIEW:
                from src.models import ManualReviewReason

                person.flag_for_review(ManualReviewReason.UKRAINE_CONNECTION_AMBIGUITY)
                self.state.manual_review.append(
                    ManualReviewRecord(
                        person=person.full_name,
                        company=person.company_name,
                        reason="Ukraine connection ambiguity",
                        person_confidence=person.person_confidence,
                        ukraine_connection_score=person.ukraine_connection.score,
                        source_urls=person.person_source_urls,
                    )
                )
        log.info("stage_verify_ukraine_connection_complete")

    # ------------------------------------------------------------------
    # Stage: VERIFY US COMPANY
    # ------------------------------------------------------------------

    def verify_us_companies(self) -> None:
        for company in self.state.companies:
            address_signals = self.us_verifier.signals_from_address(company.city, company.state, None)
            crawl_signals = self.us_verifier.signals_from_crawl_signals(company.crawl_signals)
            signals = self.us_verifier.merge_signals(address_signals, crawl_signals)
            status, score = self.us_verifier.verify(signals)
            company.us_presence_status = status
            company.crawl_signals["us_verification_score"] = score
        log.info("stage_verify_us_company_complete")

    # ------------------------------------------------------------------
    # Stage: CRAWL COMPANY WEBSITE (for companies not already crawled during
    # founder/marketer discovery)
    # ------------------------------------------------------------------

    async def crawl_company_websites(self) -> None:
        for company in self.state.companies:
            if company.crawled_pages or not company.website:
                continue
            crawl = await self.website_crawler.crawl(company.website)
            self._apply_crawl_signals(company, crawl)
        log.info("stage_crawl_company_website_complete")

    # ------------------------------------------------------------------
    # Stage: identify company_type from the people attached to it
    # ------------------------------------------------------------------

    def classify_company_types(self) -> None:
        from src.models import FOUNDER_ROLES, MARKETING_DM_ROLES

        people_by_company: dict[str, list[Person]] = {}
        for p in self.state.people:
            key = p.company_domain or p.company_name
            if key:
                people_by_company.setdefault(key, []).append(p)

        for company in self.state.companies:
            key = company.domain or company.company_name
            attached = people_by_company.get(key, [])
            has_founder = any(p.normalized_role in FOUNDER_ROLES for p in attached)
            has_marketer = any(p.normalized_role in MARKETING_DM_ROLES for p in attached)
            if has_founder and has_marketer:
                company.company_type = CompanyType.BOTH
            elif has_founder:
                company.company_type = CompanyType.UKRAINIAN_FOUNDED_US_BUSINESS
            elif has_marketer:
                company.company_type = CompanyType.US_BUSINESS_WITH_UKRAINE_CONNECTED_MARKETER
            else:
                company.company_type = CompanyType.UNKNOWN

    # ------------------------------------------------------------------
    # Stage: ACCOUNT QUALIFICATION + SEO/PPC SCORE
    # ------------------------------------------------------------------

    def qualify_accounts(self) -> None:
        people_by_company: dict[str, list[Person]] = {}
        for p in self.state.people:
            key = p.company_domain or p.company_name
            if key:
                people_by_company.setdefault(key, []).append(p)

        outbound_statuses = {UkraineConnectionStatus(s) for s in self.config.get("qualification.outbound_statuses", ["verified"])}

        for company in self.state.companies:
            company.seo_score = score_seo_opportunity(company)
            company.ppc_score = score_ppc_opportunity(company)

            key = company.domain or company.company_name
            attached = [p for p in people_by_company.get(key, []) if p.ukraine_connection.status in outbound_statuses]
            best_score = max((p.ukraine_connection.score for p in attached), default=0)

            result = self.qualification_engine.score(company, best_ukraine_connection_score=best_score)
            company.icp_score = result.icp_score
            company.account_score = result.account_score

            if attached and self.qualification_engine.qualifies(result):
                best_person = max(attached, key=lambda p: p.ukraine_connection.score)
                self.state.qualified_rows.append(
                    {
                        "company_name": company.company_name,
                        "domain": company.domain or "",
                        "website": company.website or "",
                        "city": company.city or "",
                        "state": company.state or "",
                        "country": company.country,
                        "industry": company.industry or "",
                        "employee_estimate": company.employee_estimate if company.employee_estimate is not None else "",
                        "company_type": company.company_type.value,
                        "us_presence_status": company.us_presence_status.value,
                        "account_score": company.account_score,
                        "seo_score": company.seo_score,
                        "ppc_score": company.ppc_score,
                        "qualifying_person_name": best_person.full_name,
                        "qualifying_person_role": best_person.normalized_role.value,
                        "qualifying_person_ukraine_connection_status": best_person.ukraine_connection.status.value,
                        "qualifying_person_ukraine_connection_score": best_person.ukraine_connection.score,
                        "qualifying_person_contact_channel": self._describe_contact_channel(best_person),
                        "discovery_date": company.discovery_date.isoformat(),
                    }
                )
        log.info("stage_account_qualification_complete", qualified=len(self.state.qualified_rows))

    def _describe_contact_channel(self, person: Person) -> str:
        channels = []
        for name in ("email", "phone", "linkedin", "telegram", "instagram", "facebook"):
            if getattr(person, name):
                channels.append(name)
        return ";".join(channels) if channels else "none"

    # ------------------------------------------------------------------
    # Stage: FILTER LOW-VALUE ACCOUNTS -> CONTACT ENRICHMENT
    # ------------------------------------------------------------------

    async def enrich_contacts(self) -> None:
        if not self.config.get("enrichment.enabled", True):
            return

        qualified_domains = {row["domain"] for row in self.state.qualified_rows if row["domain"]}
        qualified_names = {row["company_name"] for row in self.state.qualified_rows}
        roles_by_size = self.config.get("enrichment.roles_by_company_size", {})
        max_people = self.config.get("enrichment.max_people_per_company", 5)

        people_by_company: dict[str, list[Person]] = {}
        for p in self.state.people:
            key = p.company_domain or p.company_name
            if key:
                people_by_company.setdefault(key, []).append(p)

        for company in self.state.companies:
            key = company.domain or company.company_name
            if key not in qualified_domains and company.company_name not in qualified_names:
                continue
            people = people_by_company.get(key, [])
            if not people:
                continue
            crawl = None  # crawl results already folded into company.crawl_signals;
            # ContactWaterfall works off Person data + a CrawlResult when available.
            await self.waterfall.enrich_company_people(people, company, crawl, roles_by_size, max_people)

        log.info("stage_contact_enrichment_complete")

    # ------------------------------------------------------------------
    # Stage: CONTACT CONFIDENCE + MANUAL REVIEW
    # ------------------------------------------------------------------

    def finalize_confidence_and_manual_review(self) -> None:
        from src.models import ManualReviewReason

        for person in self.state.people:
            # person_confidence: identity-match confidence already applied
            # during dedup for merged people; for un-merged (first-seen)
            # people, seed a baseline from source count + role clarity.
            if person.person_confidence == 0.0:
                baseline = 40.0
                baseline += min(30.0, 10.0 * len(person.person_source_urls))
                if person.normalized_role != NormalizedRole.OTHER:
                    baseline += 20.0
                person.person_confidence = min(100.0, baseline)

            if person.person_confidence < 60:
                person.flag_for_review(ManualReviewReason.IDENTITY_AMBIGUITY)

            if person.normalized_role == NormalizedRole.OTHER:
                person.flag_for_review(ManualReviewReason.ROLE_UNCLEAR)

            if not person.city and not person.state:
                # location unclear is a soft signal, not disqualifying on
                # its own -- only flag it alongside another reason.
                if person.manual_review_required:
                    person.flag_for_review(ManualReviewReason.LOCATION_UNCLEAR)

            if person.manual_review_required and not any(
                r.person == person.full_name and r.reason in {rr.value for rr in person.manual_review_reasons}
                for r in self.state.manual_review
            ):
                self.state.manual_review.append(
                    ManualReviewRecord(
                        person=person.full_name,
                        company=person.company_name,
                        reason=", ".join(r.value for r in person.manual_review_reasons),
                        person_confidence=person.person_confidence,
                        ukraine_connection_score=person.ukraine_connection.score,
                        source_urls=person.person_source_urls,
                    )
                )
        log.info("stage_confidence_and_manual_review_complete", manual_review_count=len(self.state.manual_review))

    # ------------------------------------------------------------------
    # Stage: EXPORT
    # ------------------------------------------------------------------

    def export(self) -> None:
        out = self.config.output_dir
        write_companies_csv(self.state.companies, out / self.config.get("output.companies_csv", "companies.csv"))
        write_people_csv(self.state.people, out / self.config.get("output.people_csv", "people.csv"))
        write_qualified_accounts_csv(self.state.qualified_rows, out / self.config.get("output.qualified_accounts_csv", "qualified_accounts.csv"))
        write_manual_review_csv(self.state.manual_review, out / self.config.get("output.manual_review_csv", "manual_review.csv"))
        write_sources_csv(self.state.sources, out / self.config.get("output.sources_csv", "sources.csv"))
        log.info("stage_export_complete", output_dir=str(out))

    # ------------------------------------------------------------------
    # Full run
    # ------------------------------------------------------------------

    async def run(self, seed_path: str | None) -> PipelineState:
        stages: list[tuple[str, object]] = [
            ("discover_sources", lambda: self.discover_sources(seed_path)),
            ("discover_people_companies", self.discover_people_and_companies),
            ("normalize", self._sync(self.normalize)),
            ("deduplicate", self._sync(self.deduplicate)),
            ("verify_ukraine_connection", self._sync(self.verify_ukraine_connections)),
            ("verify_us_company", self._sync(self.verify_us_companies)),
            ("crawl_company_website", self.crawl_company_websites),
            ("classify_company_types", self._sync(self.classify_company_types)),
            ("account_qualification", self._sync(self.qualify_accounts)),
            ("contact_enrichment", self.enrich_contacts),
            ("manual_review", self._sync(self.finalize_confidence_and_manual_review)),
            ("export", self._sync(self.export)),
        ]

        for stage_name, fn in stages:
            if self.checkpoints and self.checkpoints.is_done(stage_name):
                log.info("stage_skipped_checkpoint", stage=stage_name)
                continue
            log.info("stage_starting", stage=stage_name)
            await fn()
            if self.checkpoints:
                self.checkpoints.mark_done(stage_name)
            self.log_writer.log("orchestrator", "stage_complete", entity_type="stage", entity_id=stage_name)

        return self.state

    @staticmethod
    def _sync(fn):
        async def wrapper():
            fn()

        return wrapper
