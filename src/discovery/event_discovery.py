"""EventDiscoveryModule (Stage 6): Ukrainian business forums/conferences/
summits in the US. Collects only public speaker/participant data (speaker
name, company, job_title, website, LinkedIn, a short bio snippet,
city/state, source_url) -- never anything behind a login or paywall.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from providers.search_provider import SearchProvider
from src.crawling.page_fetcher import PageFetcher
from src.discovery.extraction_utils import extract_person_candidates
from src.logging_setup import get_logger

log = get_logger(__name__)

EVENT_QUERY_TEMPLATES = [
    "Ukrainian business forum USA",
    "Ukrainian entrepreneur conference USA",
    "Ukrainian founders conference USA",
    "Ukraine startup event USA",
    "Ukrainian business summit USA",
    "Ukraine business conference New York",
    "Ukraine business event Chicago",
]


@dataclass
class EventSpeakerCandidate:
    full_name: str
    job_title: str | None
    company_name: str | None
    website: str | None
    linkedin: str | None
    bio_snippet: str | None
    city: str | None
    state: str | None
    source_url: str


@dataclass
class EventDiscoveryResult:
    speakers: list[EventSpeakerCandidate] = field(default_factory=list)
    event_pages: list[str] = field(default_factory=list)


class EventDiscoveryModule:
    def __init__(self, provider: SearchProvider, fetcher: PageFetcher, max_queries: int = 50):
        self.provider = provider
        self.fetcher = fetcher
        self.max_queries = max_queries

    async def discover(self, extra_queries: list[str] | None = None) -> EventDiscoveryResult:
        result = EventDiscoveryResult()
        queries = list(EVENT_QUERY_TEMPLATES) + list(extra_queries or [])
        for query in queries[: self.max_queries]:
            hits = await self.provider.search(query)
            for hit in hits:
                result.event_pages.append(hit.url)
                fetched = await self.fetcher.fetch(hit.url)
                if fetched is None:
                    continue
                _, data = fetched
                for candidate in extract_person_candidates(data, hit.url):
                    linkedin = next(
                        (link for link in candidate.get("profile_links", []) if "linkedin.com" in link), None
                    )
                    result.speakers.append(
                        EventSpeakerCandidate(
                            full_name=candidate["full_name"],
                            job_title=candidate.get("job_title"),
                            company_name=None,
                            website=None,
                            linkedin=linkedin,
                            bio_snippet=data.text_snippet[:400] if data.text_snippet else None,
                            city=None,
                            state=None,
                            source_url=hit.url,
                        )
                    )
        log.info("event_discovery_complete", speakers_found=len(result.speakers), pages=len(result.event_pages))
        return result
