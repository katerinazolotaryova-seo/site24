"""UkraineConnectionVerifier (Stage 11).

Classifies a person's public Ukraine connection from *evidence* -- text
pulled from a specific public page that is clearly about that person --
never from name/ethnicity/photo/language/school/employer inference.

How it's meant to be used
--------------------------
1. A discovery module finds a candidate person + a public page about them
   (bio page, interview, conference speaker page, company About page...).
2. The page text is passed to `extract_evidence(text, source_url, person_name)`
   which looks for strong self-identification / bio phrases *anchored to
   that person's name* (or, for a single-subject bio page, anywhere in the
   text) and returns `Evidence` objects.
3. `score_evidence(evidence_list)` aggregates evidence into a 0-100 score
   using the spec's rubric and returns a `UkraineConnection`.

Non-evidence discovery signals (a Slavic-looking surname, working at a
Ukrainian company, following Ukrainian community pages, a Ukrainian
university with no other corroboration) are exposed via
`discovery_signal(...)` -- they only ever get logged as
`DISCOVERY_SIGNAL_*` evidence, which `NON_EVIDENCE_TYPES` guarantees can
never contribute score points.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.models import Evidence, NON_EVIDENCE_TYPES, UkraineConnection, UkraineConnectionStatus, UkraineEvidenceType

# --- Strong self-identification phrases (score up to 100) ------------------
# These must be found in text that is unambiguously about the specific
# person (a single-person bio page, or a sentence whose subject resolves to
# that person's name) -- see `_phrase_is_anchored_to_person`.
SELF_ID_PHRASES = [
    r"ukrainian entrepreneur",
    r"ukrainian founder",
    r"ukrainian[- ]american entrepreneur",
    r"ukrainian[- ]american founder",
    r"founder from ukraine",
    r"originally from ukraine",
    r"born in ukraine",
    r"moved from ukraine",
    r"emigrated from ukraine",
    r"immigrated from ukraine",
    r"ukraine[- ]born entrepreneur",
    r"ukraine[- ]born founder",
    r"native of ukraine",
    r"raised in ukraine",
    r"grew up in ukraine",
    r"came to the (?:u\.?s\.?|united states) from ukraine",
]

# Evidence-type -> base score when the phrase/bio is found, per spec rubric.
EVIDENCE_TYPE_BASE_SCORE = {
    UkraineEvidenceType.SELF_IDENTIFICATION: 100,
    UkraineEvidenceType.OFFICIAL_BIOGRAPHY: 90,
    UkraineEvidenceType.CONFERENCE_BIO: 85,
    UkraineEvidenceType.FOUNDER_STORY: 85,
    UkraineEvidenceType.PROFESSIONAL_BIOGRAPHY: 80,
    UkraineEvidenceType.INTERVIEW: 75,
    UkraineEvidenceType.BUSINESS_COMMUNITY_PROFILE: 70,
    UkraineEvidenceType.PUBLIC_COMPANY_PROFILE: 65,
    UkraineEvidenceType.OTHER_PUBLIC_PROFESSIONAL_SOURCE: 55,
}

_SELF_ID_RE = re.compile("|".join(SELF_ID_PHRASES), re.IGNORECASE)


def _phrase_is_anchored_to_person(text: str, match_start: int, match_end: int, person_name: str, window: int = 220) -> bool:
    """Heuristic anchor check: is the matched phrase near a mention of the
    person's name (first or last name), OR is this a short single-subject
    bio blurb (no other proper name nearby)? This is intentionally
    conservative -- false negatives (missed evidence -> manual_review) are
    far cheaper than false positives (wrongly attributing a Ukraine
    connection to the wrong person).
    """
    lo = max(0, match_start - window)
    hi = min(len(text), match_end + window)
    context = text[lo:hi].lower()

    name_parts = [p.lower() for p in re.split(r"\s+", person_name.strip()) if len(p) > 1]
    if any(part in context for part in name_parts):
        return True

    # Single-subject bio heuristic: if the whole text is short (a speaker
    # bio / about blurb, not a long article mentioning many people), we
    # treat any self-ID phrase in it as anchored to the subject.
    if len(text) <= 1200:
        return True

    return False


def find_self_identification(text: str, person_name: str) -> list[re.Match]:
    matches = []
    for m in _SELF_ID_RE.finditer(text or ""):
        if _phrase_is_anchored_to_person(text, m.start(), m.end(), person_name):
            matches.append(m)
    return matches


def extract_evidence(
    text: str,
    source_url: str,
    person_name: str,
    evidence_type: UkraineEvidenceType = UkraineEvidenceType.OTHER_PUBLIC_PROFESSIONAL_SOURCE,
) -> list[Evidence]:
    """Scans `text` (page content already fetched from `source_url`) for
    self-identification phrases anchored to `person_name`. If found, returns
    SELF_IDENTIFICATION evidence (highest tier) regardless of the page's
    general `evidence_type`, since a direct quote always outranks the
    page-type default. If the page type itself implies a credible
    professional bio *about this person* but no exact phrase matched, the
    caller may still record page-level evidence at the lower
    `evidence_type` score by calling `record_page_level_evidence`.
    """
    out: list[Evidence] = []
    for m in find_self_identification(text, person_name):
        fragment = text[max(0, m.start() - 60): m.end() + 60].strip()
        out.append(
            Evidence(
                source_url=source_url,
                evidence_type=UkraineEvidenceType.SELF_IDENTIFICATION,
                quote_fragment=fragment,
                confidence=1.0,
            )
        )
    return out


def record_page_level_evidence(
    source_url: str,
    evidence_type: UkraineEvidenceType,
    quote_fragment: str | None = None,
    confidence: float = 0.6,
) -> Evidence:
    """Use when a page is clearly a credible bio *about the person* (e.g. an
    official company leadership bio, a conference speaker bio) that
    describes a Ukraine connection in its own words without matching one of
    our exact phrases verbatim. Caller is responsible for having actually
    read the page and confirming it is about this person and does describe
    a Ukraine connection -- this function only wraps the record, it does
    not do NLP classification.
    """
    return Evidence(
        source_url=source_url,
        evidence_type=evidence_type,
        quote_fragment=quote_fragment,
        confidence=confidence,
    )


def discovery_signal(
    source_url: str,
    signal_type: UkraineEvidenceType,
    note: str | None = None,
) -> Evidence:
    """Records a non-evidence discovery signal (surname pattern, employer
    history, language) with confidence 0 so it can never move the score,
    but is still logged for auditability / to justify why this candidate
    was queued for verification.
    """
    assert signal_type in NON_EVIDENCE_TYPES, "use record_page_level_evidence for real evidence"
    return Evidence(source_url=source_url, evidence_type=signal_type, quote_fragment=note, confidence=0.0)


@dataclass
class ScoreThresholds:
    verified: int = 85
    probable: int = 65
    manual_review: int = 40


class UkraineConnectionVerifier:
    def __init__(self, thresholds: ScoreThresholds | None = None):
        self.thresholds = thresholds or ScoreThresholds()

    def score_evidence(self, evidence_list: list[Evidence]) -> UkraineConnection:
        real_evidence = [e for e in evidence_list if e.evidence_type not in NON_EVIDENCE_TYPES]

        if not real_evidence:
            return UkraineConnection(
                status=UkraineConnectionStatus.UNKNOWN,
                connection_type=None,
                score=0,
                evidence=evidence_list,
            )

        # Best single piece of evidence sets the base score.
        def base_score(e: Evidence) -> float:
            et = e.evidence_type if isinstance(e.evidence_type, UkraineEvidenceType) else UkraineEvidenceType(e.evidence_type)
            return EVIDENCE_TYPE_BASE_SCORE.get(et, 50) * max(e.confidence, 0.5)

        best = max(real_evidence, key=base_score)
        score = round(base_score(best))

        # Two independent professional sources corroborating the connection
        # bump into the 75+ band even if neither alone was top-tier
        # (spec: "75 -- two independent professional sources").
        distinct_sources = {e.source_url for e in real_evidence}
        if len(distinct_sources) >= 2 and score < 75:
            score = max(score, 75)

        score = min(score, 100)

        status = self._status_for_score(score)
        best_et = best.evidence_type if isinstance(best.evidence_type, UkraineEvidenceType) else UkraineEvidenceType(best.evidence_type)

        return UkraineConnection(
            status=status,
            connection_type=best_et,
            score=score,
            evidence=evidence_list,
        )

    def _status_for_score(self, score: int) -> UkraineConnectionStatus:
        if score >= self.thresholds.verified:
            return UkraineConnectionStatus.VERIFIED
        if score >= self.thresholds.probable:
            return UkraineConnectionStatus.PROBABLE
        if score >= self.thresholds.manual_review:
            return UkraineConnectionStatus.MANUAL_REVIEW
        return UkraineConnectionStatus.UNKNOWN
