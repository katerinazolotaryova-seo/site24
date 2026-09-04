"""Deduplication (Stage 15).

The same company/person is routinely discovered multiple times (a directory
listing, a chamber-of-commerce page, a Google hit, a conference speaker
page, via its founder, via its CMO...). This module folds duplicate
sightings into a single canonical record using CompanyMatcher/PersonMatcher,
merging sources rather than discarding evidence.

Primary company dedup key: normalized domain. Fallback keys (name, phone,
US address) are only used when no domain is available yet -- see
CompanyMatcher.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models import Company, MatchStatus, Person
from src.processing.normalizer import normalize_company_name, normalize_domain
from src.verification.company_matcher import CompanyMatcher
from src.verification.person_matcher import PersonMatcher


@dataclass
class DedupResult:
    companies: list[Company]
    people: list[Person]
    company_merge_log: list[dict] = field(default_factory=list)
    person_merge_log: list[dict] = field(default_factory=list)
    manual_review_company_conflicts: list[dict] = field(default_factory=list)
    manual_review_person_conflicts: list[dict] = field(default_factory=list)


class Deduplicator:
    def __init__(self, company_matcher: CompanyMatcher | None = None, person_matcher: PersonMatcher | None = None):
        self.company_matcher = company_matcher or CompanyMatcher()
        self.person_matcher = person_matcher or PersonMatcher()

    # -- companies --------------------------------------------------------

    def dedupe_companies(self, companies: list[Company]) -> tuple[list[Company], list[dict], list[dict]]:
        canonical: list[Company] = []
        merge_log: list[dict] = []
        conflicts: list[dict] = []

        # Fast path: exact domain key groups first (Stage 15 primary key).
        by_domain: dict[str, list[Company]] = {}
        no_domain: list[Company] = []
        for c in companies:
            key = normalize_domain(c.domain or c.website)
            if key:
                by_domain.setdefault(key, []).append(c)
            else:
                no_domain.append(c)

        for domain, group in by_domain.items():
            merged = self._merge_company_group(group)
            canonical.append(merged)
            if len(group) > 1:
                merge_log.append({"domain": domain, "merged_count": len(group)})

        # No-domain companies: fuzzy match against canonical + each other.
        for cand in no_domain:
            match, status, breakdown = self.company_matcher.find_best_match(cand, canonical)
            if match is not None and status == MatchStatus.VERIFIED:
                self._merge_company_into(match, cand)
                merge_log.append({"domain": None, "name": cand.company_name, "merged_into": match.company_id})
            elif match is not None and status == MatchStatus.MANUAL_REVIEW:
                conflicts.append(
                    {
                        "company": cand.company_name,
                        "candidate_match": match.company_name,
                        "score": breakdown.score if breakdown else 0,
                        "reasons": breakdown.reasons if breakdown else [],
                    }
                )
                canonical.append(cand)
            else:
                canonical.append(cand)

        return canonical, merge_log, conflicts

    def _merge_company_group(self, group: list[Company]) -> Company:
        primary = group[0]
        for other in group[1:]:
            self._merge_company_into(primary, other)
        return primary

    def _merge_company_into(self, primary: Company, other: Company) -> None:
        for src in other.company_source:
            primary.merge_source(src)
        primary.website = primary.website or other.website
        primary.domain = primary.domain or other.domain
        primary.city = primary.city or other.city
        primary.state = primary.state or other.state
        primary.industry = primary.industry or other.industry
        primary.employee_estimate = primary.employee_estimate or other.employee_estimate
        primary.us_presence_evidence.extend(other.us_presence_evidence)
        for page in other.crawled_pages:
            if page not in primary.crawled_pages:
                primary.crawled_pages.append(page)
        primary.crawl_signals = {**other.crawl_signals, **primary.crawl_signals}

    # -- people -------------------------------------------------------------

    def dedupe_people(self, people: list[Person]) -> tuple[list[Person], list[dict], list[dict]]:
        canonical: list[Person] = []
        merge_log: list[dict] = []
        conflicts: list[dict] = []

        # Group by normalized name first to keep the matcher's search space
        # small (never compare two people with completely different names).
        by_name: dict[str, list[Person]] = {}
        for p in people:
            key = normalize_company_name(p.full_name)  # reuse generic normalizer
            by_name.setdefault(key, []).append(p)

        for _, group in by_name.items():
            bucket: list[Person] = []
            for cand in group:
                match, status, breakdown = self.person_matcher.find_best_match(cand, bucket)
                if match is not None and status == MatchStatus.VERIFIED:
                    self._merge_person_into(match, cand)
                    merge_log.append({"name": cand.full_name, "merged_into": match.person_id})
                elif match is not None and status == MatchStatus.MANUAL_REVIEW:
                    conflicts.append(
                        {
                            "person": cand.full_name,
                            "candidate_match": match.full_name,
                            "score": breakdown.score if breakdown else 0,
                            "reasons": breakdown.reasons if breakdown else [],
                        }
                    )
                    cand.flag_for_review(_reason_for("identity ambiguity"))
                    bucket.append(cand)
                else:
                    bucket.append(cand)
            canonical.extend(bucket)

        return canonical, merge_log, conflicts

    def _merge_person_into(self, primary: Person, other: Person) -> None:
        for url in other.person_source_urls:
            primary.add_source_url(url)
        primary.linkedin = primary.linkedin or other.linkedin
        primary.telegram = primary.telegram or other.telegram
        primary.instagram = primary.instagram or other.instagram
        primary.facebook = primary.facebook or other.facebook
        primary.email = primary.email or other.email
        primary.phone = primary.phone or other.phone
        primary.city = primary.city or other.city
        primary.state = primary.state or other.state
        primary.ukraine_connection.evidence.extend(other.ukraine_connection.evidence)


def _reason_for(text: str):
    from src.models import ManualReviewReason

    for r in ManualReviewReason:
        if r.value == text:
            return r
    return ManualReviewReason.IDENTITY_AMBIGUITY
