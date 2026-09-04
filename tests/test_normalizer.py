from src.processing.normalizer import (
    normalize_company_name,
    normalize_domain,
    normalize_person_name,
    normalize_phone,
)


def test_normalize_domain_strips_scheme_www_path():
    assert normalize_domain("https://www.acme.com/about") == "acme.com"
    assert normalize_domain("acme.com") == "acme.com"
    assert normalize_domain(None) is None
    assert normalize_domain("not a url") is None


def test_normalize_company_name_strips_legal_suffix_and_case():
    assert normalize_company_name("Acme, Inc.") == "acme"
    assert normalize_company_name("The Acme Group LLC") == "acme"


def test_normalize_person_name_strips_credentials():
    assert normalize_person_name("Jane Smith, MBA") == "Jane Smith"


def test_normalize_phone():
    assert normalize_phone("(212) 555-0100") == "2125550100"
    assert normalize_phone("+1 212 555 0100") == "+12125550100"
    assert normalize_phone("123") is None
    assert normalize_phone(None) is None
