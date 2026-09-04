"""Phone discovery for a Person -- company/business/direct lines only,
sourced from the crawled site or Apollo, never guessed.
"""

from __future__ import annotations

from typing import Optional

from providers.apollo import ApolloProvider
from src.crawling.website_crawler import CrawlResult
from src.models import FieldValue
from src.processing.normalizer import normalize_phone


def phone_from_crawl(crawl: CrawlResult | None, source_url: str | None = None) -> Optional[FieldValue]:
    """Company-level business phone found during the site crawl (usually
    from /contact). This is a lower-confidence "business line", not
    necessarily the person's direct line -- callers should label it as such.
    """
    if crawl is None:
        return None
    phones = crawl.merged_phones()
    if not phones:
        return None
    raw = sorted(phones)[0]
    normalized = normalize_phone(raw)
    if not normalized:
        return None
    return FieldValue(value=normalized, source_url=source_url or crawl.domain, confidence=0.6, provider="website_crawl")


async def phone_from_apollo(apollo: ApolloProvider, full_name: str, domain: str) -> Optional[FieldValue]:
    if not domain:
        return None
    result = await apollo.enrich_person(full_name, domain)
    if not result or "phone" not in result:
        return None
    phone_data = result["phone"]
    return FieldValue(value=phone_data["phone"], confidence=phone_data["confidence"], provider="apollo")
