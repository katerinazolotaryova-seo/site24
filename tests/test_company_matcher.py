from src.models import Company, MatchStatus
from src.verification.company_matcher import CompanyMatcher


def test_same_domain_is_verified():
    matcher = CompanyMatcher()
    a = Company(company_name="Acme Inc", website="https://acme.com")
    b = Company(company_name="Acme, Inc.", website="https://www.acme.com/about")
    status, breakdown = matcher.is_same_company(a, b)
    assert status == MatchStatus.VERIFIED
    assert breakdown.score >= 80


def test_different_domains_reject_even_with_similar_name():
    matcher = CompanyMatcher()
    a = Company(company_name="Acme Inc", website="https://acme.com")
    b = Company(company_name="Acme Inc", website="https://acme-consulting.io")
    status, _ = matcher.is_same_company(a, b)
    assert status == MatchStatus.REJECT


def test_no_domain_falls_back_to_fuzzy_name_and_address():
    matcher = CompanyMatcher()
    a = Company(company_name="Kyiv Bakery LLC", city="Chicago", state="Illinois")
    b = Company(company_name="Kyiv Bakery", city="Chicago", state="Illinois")
    status, breakdown = matcher.is_same_company(a, b)
    assert status in (MatchStatus.VERIFIED, MatchStatus.PROBABLE)
    assert breakdown.score >= 60
