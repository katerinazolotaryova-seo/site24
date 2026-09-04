"""SearchDiscoveryEngine (Stages 2-4): generates and runs the general,
state-level and city-level "Ukrainian founder/entrepreneur/business owner"
search-query masks, and hands back raw search hits for downstream
founder/company extraction.

Query generation is pure (no network, fully unit-testable); running the
queries goes through `providers.search_provider.SearchProvider`, which is a
no-op in dry-run/no-backend mode.
"""

from __future__ import annotations

from dataclasses import dataclass

from providers.search_provider import SearchProvider, SearchResult
from src.logging_setup import get_logger

log = get_logger(__name__)

GENERAL_QUERY_TEMPLATES = [
    '"Ukrainian founder" USA',
    '"Ukrainian entrepreneur" USA',
    '"Ukrainian-owned business" USA',
    '"Ukrainian business owner" USA',
    '"founder from Ukraine" USA',
    '"Ukrainian-founded company" USA',
    '"Ukrainian founders" USA',
    '"Ukrainian startup founder" USA',
]

STATE_QUERY_TEMPLATES = [
    '"Ukrainian founder" {place}',
    '"Ukrainian entrepreneur" {place}',
    '"Ukrainian-owned business" {place}',
    '"founder from Ukraine" {place}',
    '"Ukrainian business owner" {place}',
    '"Ukrainian startup" {place}',
]

CITY_QUERY_TEMPLATES = [
    '"Ukrainian founder" {place}',
    '"Ukrainian entrepreneur" {place}',
    '"Ukrainian-owned business" {place}',
    '"Ukrainian business owner" {place}',
]


@dataclass
class GeneratedQuery:
    query: str
    stage: str  # general | state | city
    place: str | None = None


def build_general_queries() -> list[GeneratedQuery]:
    return [GeneratedQuery(query=q, stage="general") for q in GENERAL_QUERY_TEMPLATES]


def build_state_queries(states: list[str]) -> list[GeneratedQuery]:
    out = []
    for state in states:
        for template in STATE_QUERY_TEMPLATES:
            out.append(GeneratedQuery(query=template.format(place=state), stage="state", place=state))
    return out


def build_city_queries(cities: list[dict]) -> list[GeneratedQuery]:
    out = []
    for city in cities:
        name = city.get("name") if isinstance(city, dict) else city
        for template in CITY_QUERY_TEMPLATES:
            out.append(GeneratedQuery(query=template.format(place=name), stage="city", place=name))
    return out


class SearchDiscoveryEngine:
    def __init__(self, provider: SearchProvider, max_queries_per_stage: int = 200):
        self.provider = provider
        self.max_queries_per_stage = max_queries_per_stage

    async def run_queries(self, queries: list[GeneratedQuery]) -> list[SearchResult]:
        capped = queries[: self.max_queries_per_stage]
        results: list[SearchResult] = []
        for q in capped:
            hits = await self.provider.search(q.query)
            results.extend(hits)
            log.debug("search_query_executed", query=q.query, stage=q.stage, place=q.place, hit_count=len(hits))
        return results

    async def discover_general(self) -> list[SearchResult]:
        return await self.run_queries(build_general_queries())

    async def discover_states(self, states: list[str]) -> list[SearchResult]:
        return await self.run_queries(build_state_queries(states))

    async def discover_cities(self, cities: list[dict]) -> list[SearchResult]:
        return await self.run_queries(build_city_queries(cities))
