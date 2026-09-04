"""Public social profile discovery (LinkedIn, Telegram, Instagram,
Facebook) -- only ever from links that were actually published on a public
page (company site, directory, event page). Never guesses handles.
"""

from __future__ import annotations

from typing import Optional

from src.crawling.website_crawler import CrawlResult
from src.models import FieldValue

_PLATFORM_FIELDS = ("linkedin", "telegram", "instagram", "facebook")


def socials_from_crawl(crawl: CrawlResult | None, source_url: str | None = None) -> dict[str, FieldValue]:
    if crawl is None:
        return {}
    merged = crawl.merged_social()
    out: dict[str, FieldValue] = {}
    for platform in _PLATFORM_FIELDS:
        links = merged.get(platform)
        if links:
            link = sorted(links)[0]
            out[platform] = FieldValue(value=link, source_url=source_url or crawl.domain, confidence=0.8, provider="website_crawl")
    return out


def socials_from_apollo_result(apollo_result: Optional[dict]) -> dict[str, FieldValue]:
    if not apollo_result or "linkedin" not in apollo_result:
        return {}
    data = apollo_result["linkedin"]
    return {"linkedin": FieldValue(value=data["linkedin"], confidence=data["confidence"], provider="apollo")}
