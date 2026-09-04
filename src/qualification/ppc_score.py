"""PPC Opportunity Score (Stage 16), 0-100.

Signals read from Company.crawl_signals (all optional booleans/numbers,
populated by the website crawler / structured_data_parser):

    commercial_intent: bool         # pricing/buy/quote/demo pages present
    is_ecommerce: bool
    product_catalog_size: int
    high_value_services: bool       # e.g. B2B services, high AOV/LTV signals
    multiple_markets: bool
    has_google_ads_tag: bool
    has_meta_pixel: bool
    has_google_analytics: bool
    has_conversion_tracking: bool
    landing_page_count: int
    multi_location: bool
    high_ltv_business: bool
"""

from __future__ import annotations

from src.models import Company

BOOL_WEIGHTS = {
    "commercial_intent": 15,
    "is_ecommerce": 15,
    "high_value_services": 10,
    "multiple_markets": 8,
    "has_google_ads_tag": 12,
    "has_meta_pixel": 8,
    "has_google_analytics": 5,
    "has_conversion_tracking": 10,
    "multi_location": 5,
    "high_ltv_business": 12,
}


def score_ppc_opportunity(company: Company) -> int:
    signals = company.crawl_signals or {}
    score = 0

    for key, weight in BOOL_WEIGHTS.items():
        if signals.get(key):
            score += weight

    catalog_size = int(signals.get("product_catalog_size", 0) or 0)
    score += min(10, catalog_size // 20)  # every ~20 SKUs, up to +10

    landing_pages = int(signals.get("landing_page_count", 0) or 0)
    score += min(10, landing_pages * 2)

    return max(0, min(100, score))
