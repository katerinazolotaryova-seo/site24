"""Email discovery for a Person, following the "official website first"
principle -- never guessing/generating addresses ourselves.
"""

from __future__ import annotations

from typing import Optional

from providers.hunter import HunterProvider
from src.crawling.website_crawler import CrawlResult
from src.models import FieldValue

_COMMON_ROLE_ADDRESSES = {"info", "contact", "hello", "sales", "support", "team", "press"}


def email_from_crawl(person_full_name: str, crawl: CrawlResult | None, source_url: str | None = None) -> Optional[FieldValue]:
    """Looks for an email on the company's own crawled pages that plausibly
    belongs to this person (contains a name token before the @, and is not
    a generic role address like info@/contact@).
    """
    if crawl is None:
        return None
    name_tokens = [t.lower() for t in person_full_name.split() if len(t) > 1]
    if not name_tokens:
        return None

    for email in crawl.merged_emails():
        local_part = email.split("@")[0].lower()
        if local_part in _COMMON_ROLE_ADDRESSES:
            continue
        if any(tok in local_part for tok in name_tokens):
            return FieldValue(value=email, source_url=source_url or crawl.domain, confidence=0.9, provider="website_crawl")
    return None


async def email_from_hunter(hunter: HunterProvider, domain: str, full_name: str) -> Optional[FieldValue]:
    if not domain:
        return None
    result = await hunter.find_email(domain, full_name)
    if not result:
        return None
    return FieldValue(value=result["email"], confidence=result["confidence"], provider="hunter")
