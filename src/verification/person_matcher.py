"""PersonMatcher (Stage 14): decides whether two person "sightings" (from
different sources) are the same human being, so we never merge two
different people who happen to share a name (the classic "John Smith"
problem) and never split one real person into duplicate records.

Scoring per spec:
    exact full name                 +25
    current company exact match     +30
    job title match                 +20
    location match                  +10
    official company link           +20
    matching biography              +20
    same verified social username   +10

Thresholds:
    >=80 verified
    60-79 probable
    40-59 manual_review
    <40 reject
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rapidfuzz import fuzz

from src.models import MatchStatus, Person
from src.processing.normalizer import normalize_company_name, normalize_domain, normalize_person_name


@dataclass
class MatchScoreBreakdown:
    score: int = 0
    reasons: list[str] = field(default_factory=list)

    def add(self, points: int, reason: str) -> None:
        if points:
            self.score += points
            self.reasons.append(f"{reason}:{points:+d}")


NAME_EXACT_THRESHOLD = 97  # rapidfuzz token_sort_ratio; treat near-identical as "exact"


class PersonMatcher:
    def __init__(
        self,
        verified_threshold: int = 80,
        probable_threshold: int = 60,
        manual_review_threshold: int = 40,
    ):
        self.verified_threshold = verified_threshold
        self.probable_threshold = probable_threshold
        self.manual_review_threshold = manual_review_threshold

    def score(self, candidate: Person, existing: Person) -> MatchScoreBreakdown:
        breakdown = MatchScoreBreakdown()

        name_similarity = fuzz.token_sort_ratio(
            normalize_person_name(candidate.full_name).lower(),
            normalize_person_name(existing.full_name).lower(),
        )
        if name_similarity >= NAME_EXACT_THRESHOLD:
            breakdown.add(25, "exact_full_name")
        elif name_similarity < 70:
            # Names don't even fuzzy-match -- treat as almost certainly a
            # different person regardless of other signals.
            breakdown.add(0, "name_mismatch")
            return breakdown

        cand_domain = normalize_domain(candidate.company_domain) if candidate.company_domain else None
        exist_domain = normalize_domain(existing.company_domain) if existing.company_domain else None
        if cand_domain and exist_domain and cand_domain == exist_domain:
            breakdown.add(30, "current_company_exact_match")
        elif (
            not cand_domain
            and not exist_domain
            and candidate.company_name
            and existing.company_name
            and normalize_company_name(candidate.company_name) == normalize_company_name(existing.company_name)
        ):
            breakdown.add(30, "current_company_exact_match")

        if candidate.normalized_role == existing.normalized_role and candidate.normalized_role.value != "other":
            breakdown.add(20, "job_title_match")

        if (
            candidate.city
            and existing.city
            and candidate.city.lower() == existing.city.lower()
            and candidate.state
            and existing.state
            and candidate.state.lower() == existing.state.lower()
        ):
            breakdown.add(10, "location_match")

        if candidate.company_id and existing.company_id and candidate.company_id == existing.company_id:
            breakdown.add(20, "official_company_link")

        for field_name in ("linkedin", "telegram", "instagram", "facebook"):
            cand_field = getattr(candidate, field_name)
            exist_field = getattr(existing, field_name)
            if cand_field and exist_field and cand_field.value.strip().lower() == exist_field.value.strip().lower():
                breakdown.add(10, f"same_verified_social:{field_name}")
                break

        return breakdown

    def match_status(self, score: int) -> MatchStatus:
        if score >= self.verified_threshold:
            return MatchStatus.VERIFIED
        if score >= self.probable_threshold:
            return MatchStatus.PROBABLE
        if score >= self.manual_review_threshold:
            return MatchStatus.MANUAL_REVIEW
        return MatchStatus.REJECT

    def is_same_person(self, candidate: Person, existing: Person) -> tuple[MatchStatus, MatchScoreBreakdown]:
        breakdown = self.score(candidate, existing)
        return self.match_status(breakdown.score), breakdown

    def find_best_match(self, candidate: Person, pool: list[Person]) -> tuple[Person | None, MatchStatus, MatchScoreBreakdown | None]:
        """Finds the best-matching existing Person for `candidate` among
        `pool` (typically people already collected for the same company).
        """
        best: tuple[Person, MatchStatus, MatchScoreBreakdown] | None = None
        for existing in pool:
            status, breakdown = self.is_same_person(candidate, existing)
            if best is None or breakdown.score > best[2].score:
                best = (existing, status, breakdown)
        if best is None:
            return None, MatchStatus.REJECT, None
        return best
