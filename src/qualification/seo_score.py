"""SEO Opportunity Score (Stage 16), 0-100.

Consumes `Company.crawl_signals` -- a dict populated by
crawling/structured_data_parser.py + page_classifier.py while crawling the
company's site. Each boolean/numeric signal below is optional; the score
degrades gracefully when a signal wasn't collected (crawl failed, site
blocked, etc.) rather than crashing.

Signals read from crawl_signals (all optional):
    indexable_commercial_pages: int
    has_category_structure: bool
    has_blog: bool
    blog_post_count: int
    multi_location: bool
    multi_language: bool
    weak_title_coverage: bool     # many pages missing/duplicate <title>
    thin_commercial_pages: bool   # low word count on money pages
    large_site: bool              # rough page-count signal
    international_presence: bool
    competitive_industry: bool
"""

from __future__ import annotations

from src.models import Company

# Positive opportunity signals: the more of these present, the more SEO
# upside a well-executed engagement has (an established but neglected site
# beats a 3-page brochure site with nothing to optimize).
POSITIVE_WEIGHTS = {
    "has_category_structure": 15,
    "has_blog": 10,
    "multi_location": 10,
    "multi_language": 8,
    "large_site": 10,
    "international_presence": 7,
    "competitive_industry": 10,
}

# Signals that indicate *problems* worth fixing == opportunity for an SEO
# engagement, so they also add points (a perfectly optimized site has
# little SEO upside left to sell).
PROBLEM_WEIGHTS = {
    "weak_title_coverage": 15,
    "thin_commercial_pages": 15,
}


def score_seo_opportunity(company: Company) -> int:
    signals = company.crawl_signals or {}
    score = 0

    commercial_pages = int(signals.get("indexable_commercial_pages", 0) or 0)
    score += min(20, commercial_pages * 2)  # up to 10 commercial pages = full 20

    blog_posts = int(signals.get("blog_post_count", 0) or 0)
    score += min(10, blog_posts)  # content presence, capped

    for key, weight in POSITIVE_WEIGHTS.items():
        if signals.get(key):
            score += weight

    for key, weight in PROBLEM_WEIGHTS.items():
        if signals.get(key):
            score += weight

    return max(0, min(100, score))
