from src.models import MatchStatus, NormalizedRole, Person
from src.verification.person_matcher import PersonMatcher


def make_person(**kwargs) -> Person:
    defaults = dict(full_name="John Smith", normalized_role=NormalizedRole.CMO)
    defaults.update(kwargs)
    return Person(**defaults)


def test_same_person_same_company_verified():
    matcher = PersonMatcher()
    a = make_person(company_domain="acme.com", city="Austin", state="Texas")
    b = make_person(company_domain="acme.com", city="Austin", state="Texas")
    status, breakdown = matcher.is_same_person(a, b)
    assert status == MatchStatus.VERIFIED
    assert breakdown.score >= 80


def test_same_name_different_company_is_not_verified():
    """The classic John Smith problem: same name, unrelated companies."""
    matcher = PersonMatcher()
    a = make_person(company_domain="acme.com", normalized_role=NormalizedRole.CMO)
    b = make_person(company_domain="other-corp.com", normalized_role=NormalizedRole.HEAD_OF_GROWTH, city="Miami", state="Florida")
    status, breakdown = matcher.is_same_person(a, b)
    assert status != MatchStatus.VERIFIED
    assert breakdown.score < 80


def test_different_names_reject():
    matcher = PersonMatcher()
    a = make_person(full_name="John Smith")
    b = make_person(full_name="Olena Kovalenko")
    status, _ = matcher.is_same_person(a, b)
    assert status == MatchStatus.REJECT


def test_find_best_match_picks_highest_score():
    matcher = PersonMatcher()
    candidate = make_person(company_domain="acme.com", city="Austin", state="Texas")
    pool = [
        make_person(full_name="Someone Else"),
        make_person(company_domain="acme.com", city="Austin", state="Texas"),
    ]
    match, status, breakdown = matcher.find_best_match(candidate, pool)
    assert match is pool[1]
    assert status == MatchStatus.VERIFIED
