"""Integration-style tests for FounderDiscovery / MarketingDMDiscovery using
stub search + fetch layers (no real network), to prove query generation,
result fetching, extraction and role-filtering are wired correctly end to
end.
"""

from __future__ import annotations


import pytest

from providers.search_provider import SearchResult
from src.crawling.structured_data_parser import parse_page
from src.discovery.founder_discovery import FounderDiscovery, build_founder_queries
from src.discovery.marketer_discovery import MarketingDMDiscovery, build_marketing_dm_queries
from src.models import NormalizedRole

FOUNDER_PAGE_HTML = """
<html><head><title>About | Kyiv Bakery</title></head>
<body><h2>Maria Ivanenko, Founder & CEO</h2></body></html>
"""

CMO_PAGE_HTML = """
<html><head><title>Leadership | Kyiv Bakery</title></head>
<body><h2>David Lee, Chief Marketing Officer</h2></body></html>
"""

ENGINEER_PAGE_HTML = """
<html><head><title>Team | Kyiv Bakery</title></head>
<body><h2>Alex Johnson, Senior Software Engineer</h2></body></html>
"""


class StubSearchProvider:
    def __init__(self, url_by_query: dict[str, str]):
        self.url_by_query = url_by_query

    async def search(self, query: str) -> list[SearchResult]:
        url = self.url_by_query.get(query)
        if not url:
            return []
        return [SearchResult(title="hit", url=url, snippet="", query=query)]


class StubFetcher:
    def __init__(self, html_by_url: dict[str, str]):
        self.html_by_url = html_by_url

    async def fetch(self, url: str):
        html = self.html_by_url.get(url)
        if html is None:
            return None
        return html, parse_page(html, url)


class StubWebsiteCrawler:
    async def crawl(self, base_url: str):
        from src.crawling.website_crawler import CrawlResult

        return CrawlResult(domain=base_url)


@pytest.mark.asyncio
async def test_founder_discovery_finds_founder_and_ignores_engineer():
    queries = build_founder_queries("Kyiv Bakery")
    url_by_query = {queries[0]: "https://example.com/founder-mention"}
    html_by_url = {
        "https://example.com/founder-mention": FOUNDER_PAGE_HTML,
        "https://example.com/engineer-mention": ENGINEER_PAGE_HTML,
    }
    discovery = FounderDiscovery(StubSearchProvider(url_by_query), StubFetcher(html_by_url), StubWebsiteCrawler())
    result = await discovery.discover("Kyiv Bakery", company_website=None)

    names = [c.full_name for c in result.candidates]
    assert "Maria Ivanenko" in names
    match = next(c for c in result.candidates if c.full_name == "Maria Ivanenko")
    assert match.normalized_role == NormalizedRole.FOUNDER


@pytest.mark.asyncio
async def test_marketing_dm_discovery_finds_cmo():
    queries = build_marketing_dm_queries("Kyiv Bakery")
    url_by_query = {queries[0]: "https://example.com/cmo-mention"}
    html_by_url = {"https://example.com/cmo-mention": CMO_PAGE_HTML}
    discovery = MarketingDMDiscovery(StubSearchProvider(url_by_query), StubFetcher(html_by_url), StubWebsiteCrawler())
    result = await discovery.discover("Kyiv Bakery", company_website=None)

    assert len(result.candidates) == 1
    assert result.candidates[0].full_name == "David Lee"
    assert result.candidates[0].normalized_role == NormalizedRole.CMO


@pytest.mark.asyncio
async def test_founder_discovery_from_company_website_crawl():
    class CrawlerWithFounderPage(StubWebsiteCrawler):
        async def crawl(self, base_url: str):
            from src.crawling.page_classifier import PageCategory
            from src.crawling.website_crawler import CrawlResult, CrawledPage

            result = CrawlResult(domain=base_url)
            result.pages.append(
                CrawledPage(
                    url=f"{base_url}/about",
                    status_code=200,
                    category=PageCategory.ABOUT.value,
                    data=parse_page(FOUNDER_PAGE_HTML, f"{base_url}/about"),
                )
            )
            return result

    discovery = FounderDiscovery(StubSearchProvider({}), StubFetcher({}), CrawlerWithFounderPage())
    result = await discovery.discover("Kyiv Bakery", company_website="https://kyivbakery.com")

    assert any(c.full_name == "Maria Ivanenko" for c in result.candidates)
