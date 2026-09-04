from src.models import UkraineConnectionStatus, UkraineEvidenceType
from src.verification.ukraine_connection import (
    UkraineConnectionVerifier,
    discovery_signal,
    extract_evidence,
    record_page_level_evidence,
)


def test_self_identification_phrase_scores_verified():
    text = "Jane Kovalenko is a Ukrainian entrepreneur who built her company from scratch."
    evidence = extract_evidence(text, "https://example.com/bio", "Jane Kovalenko")
    assert evidence, "expected a self-identification match"
    verifier = UkraineConnectionVerifier()
    result = verifier.score_evidence(evidence)
    assert result.status == UkraineConnectionStatus.VERIFIED
    assert result.score >= 85


def test_no_evidence_stays_unknown():
    verifier = UkraineConnectionVerifier()
    result = verifier.score_evidence([])
    assert result.status == UkraineConnectionStatus.UNKNOWN
    assert result.score == 0


def test_discovery_signal_alone_never_scores():
    signal = discovery_signal("https://example.com", UkraineEvidenceType.DISCOVERY_SIGNAL_EMPLOYER, "worked at MacPaw")
    verifier = UkraineConnectionVerifier()
    result = verifier.score_evidence([signal])
    assert result.status == UkraineConnectionStatus.UNKNOWN
    assert result.score == 0


def test_two_independent_professional_sources_reach_probable_band():
    evidence = [
        record_page_level_evidence("https://source1.com/bio", UkraineEvidenceType.OTHER_PUBLIC_PROFESSIONAL_SOURCE, confidence=0.6),
        record_page_level_evidence("https://source2.com/profile", UkraineEvidenceType.OTHER_PUBLIC_PROFESSIONAL_SOURCE, confidence=0.6),
    ]
    verifier = UkraineConnectionVerifier()
    result = verifier.score_evidence(evidence)
    assert result.score >= 75
    assert result.status in (UkraineConnectionStatus.VERIFIED, UkraineConnectionStatus.PROBABLE)


def test_phrase_not_anchored_to_wrong_person_in_long_article():
    # A long article about someone else that happens to mention Ukraine
    # should not be anchored to an unrelated person's name.
    long_text = (
        "A" * 1300
        + " John Smith met with a Ukrainian entrepreneur at a conference last week to discuss trade policy."
    )
    evidence = extract_evidence(long_text, "https://news.example.com/article", "Bob Someone Else")
    assert evidence == []


def test_ukraine_word_in_snippet_alone_is_not_evidence():
    # Simulates a raw search snippet -- callers must never pass a snippet
    # straight to extract_evidence and treat it as evidence without first
    # confirming it's page content about the person; but even so, a bare
    # mention of "Ukraine" without one of the strong phrases should not
    # produce evidence.
    snippet = "Company hires new CMO, previously worked with partners in Ukraine on logistics."
    evidence = extract_evidence(snippet, "https://example.com/press", "Some Person")
    assert evidence == []
