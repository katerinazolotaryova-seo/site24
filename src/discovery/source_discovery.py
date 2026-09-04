"""Source discovery: Stage 1 (seed ingestion) + Stage 5 (community
discovery, growing the source queue from search results).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from providers.search_provider import SearchProvider
from src.crawling.page_classifier import classify_path, is_person_bearing
from src.logging_setup import get_logger
from src.models import DiscoverySource

log = get_logger(__name__)

COMMUNITY_QUERY_TEMPLATES = [
    "Ukrainian business association USA",
    "Ukrainian entrepreneur community USA",
    "Ukrainian business club USA",
    "Ukrainian founders USA",
    "Ukrainian business network USA",
]

COMMUNITY_CITY_QUERY_TEMPLATES = [
    "Ukrainian entrepreneurs {place}",
    "Ukrainian business club {place}",
    "Ukrainian founders {place}",
]


def load_seed_sources(csv_path: str | Path) -> list[DiscoverySource]:
    path = Path(csv_path)
    if not path.exists():
        log.warning("seed_sources_file_missing", path=str(path))
        return []
    sources: list[DiscoverySource] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("source_name") or "").strip()
            url = (row.get("source_url") or "").strip()
            source_type = (row.get("source_type") or "other").strip()
            if not name or not url:
                continue
            sources.append(
                DiscoverySource(
                    source_name=name,
                    source_url=url,
                    source_type=source_type,
                    discovered_via="seed_file",
                )
            )
    log.info("seed_sources_loaded", count=len(sources), path=str(path))
    return sources


def build_community_queries(cities: list[str] | None = None) -> list[str]:
    queries = list(COMMUNITY_QUERY_TEMPLATES)
    for city in cities or []:
        for template in COMMUNITY_CITY_QUERY_TEMPLATES:
            queries.append(template.format(place=city))
    return queries


@dataclass
class CommunityDiscoveryResult:
    new_sources: list[DiscoverySource] = field(default_factory=list)


class CommunityDiscovery:
    """Runs the Stage 5 community-discovery search queries, classifies each
    hit's page type (members/directory/board/leadership/speakers/
    participants/sponsors/partners/companies/founders) and queues any that
    look like a real source for directory_discovery to process.
    """

    def __init__(self, provider: SearchProvider):
        self.provider = provider

    async def discover(self, cities: list[str] | None = None) -> CommunityDiscoveryResult:
        result = CommunityDiscoveryResult()
        seen_domains: set[str] = set()
        for query in build_community_queries(cities):
            hits = await self.provider.search(query)
            for hit in hits:
                parsed = urlparse(hit.url)
                if not parsed.netloc:
                    continue
                category = classify_path(parsed.path)
                if not is_person_bearing(category) and parsed.path not in ("", "/"):
                    continue
                if parsed.netloc in seen_domains:
                    continue
                seen_domains.add(parsed.netloc)
                result.new_sources.append(
                    DiscoverySource(
                        source_name=hit.title or parsed.netloc,
                        source_url=f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
                        source_type="community",
                        discovered_via=f"community_search:{query}",
                        pages_classified=[category.value],
                    )
                )
        log.info("community_discovery_complete", new_sources=len(result.new_sources))
        return result
