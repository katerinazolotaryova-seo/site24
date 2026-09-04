"""CompanyMatcher: identity resolution between two company "sightings"
found via different discovery paths (UA2USA, a chamber directory, Google,
a conference, via its founder, via its CMO, ...). Feeds Stage 15
deduplication. Domain is the primary key; name/phone/address are fallback
signals for companies discovered without a domain yet (e.g. a name-only
mention on a conference speaker page).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rapidfuzz import fuzz

from src.models import Company, MatchStatus
from src.processing.normalizer import normalize_company_name, normalize_domain, normalize_phone

NAME_EXACT_THRESHOLD = 95


@dataclass
class CompanyMatchScoreBreakdown:
    score: int = 0
    reasons: list[str] = field(default_factory=list)

    def add(self, points: int, reason: str) -> None:
        if points:
            self.score += points
            self.reasons.append(f"{reason}:{points:+d}")


class CompanyMatcher:
    def __init__(
        self,
        verified_threshold: int = 80,
        probable_threshold: int = 60,
        manual_review_threshold: int = 40,
    ):
        self.verified_threshold = verified_threshold
        self.probable_threshold = probable_threshold
        self.manual_review_threshold = manual_review_threshold

    def score(self, candidate: Company, existing: Company) -> CompanyMatchScoreBreakdown:
        breakdown = CompanyMatchScoreBreakdown()

        cand_domain = normalize_domain(candidate.domain or candidate.website)
        exist_domain = normalize_domain(existing.domain or existing.website)
        if cand_domain and exist_domain:
            if cand_domain == exist_domain:
                breakdown.add(90, "domain_exact_match")
                return breakdown  # domain match is decisive on its own
            else:
                breakdown.add(0, "domain_mismatch")
                return breakdown  # different domains -> different companies

        name_similarity = fuzz.token_sort_ratio(
            normalize_company_name(candidate.company_name),
            normalize_company_name(existing.company_name),
        )
        if name_similarity >= NAME_EXACT_THRESHOLD:
            breakdown.add(45, "normalized_name_match")
        elif name_similarity >= 85:
            breakdown.add(25, "fuzzy_name_match")
        elif name_similarity < 60:
            breakdown.add(0, "name_mismatch")
            return breakdown

        cand_phone = normalize_phone(candidate.crawl_signals.get("phone")) if candidate.crawl_signals else None
        exist_phone = normalize_phone(existing.crawl_signals.get("phone")) if existing.crawl_signals else None
        if cand_phone and exist_phone and cand_phone == exist_phone:
            breakdown.add(25, "phone_match")

        if (
            candidate.city
            and existing.city
            and candidate.city.lower() == existing.city.lower()
            and candidate.state
            and existing.state
            and candidate.state.lower() == existing.state.lower()
        ):
            breakdown.add(15, "us_address_match")

        return breakdown

    def match_status(self, score: int) -> MatchStatus:
        if score >= self.verified_threshold:
            return MatchStatus.VERIFIED
        if score >= self.probable_threshold:
            return MatchStatus.PROBABLE
        if score >= self.manual_review_threshold:
            return MatchStatus.MANUAL_REVIEW
        return MatchStatus.REJECT

    def is_same_company(self, candidate: Company, existing: Company) -> tuple[MatchStatus, CompanyMatchScoreBreakdown]:
        breakdown = self.score(candidate, existing)
        return self.match_status(breakdown.score), breakdown

    def find_best_match(self, candidate: Company, pool: list[Company]) -> tuple[Company | None, MatchStatus, CompanyMatchScoreBreakdown | None]:
        best: tuple[Company, MatchStatus, CompanyMatchScoreBreakdown] | None = None
        for existing in pool:
            status, breakdown = self.is_same_company(candidate, existing)
            if best is None or breakdown.score > best[2].score:
                best = (existing, status, breakdown)
        if best is None:
            return None, MatchStatus.REJECT, None
        return best
