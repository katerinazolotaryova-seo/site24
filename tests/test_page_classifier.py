from src.crawling.page_classifier import PageCategory, classify_path


def test_company_vs_companies_no_longer_collide():
    """Regression test: a naive substring match on "/company" used to also
    match inside "/companies" (and inside unrelated URLs merely containing
    "company" as a substring of a longer word), silently miscategorizing
    listing pages as single-company pages. Caught during a live Stage 1
    run against usubc.org, where this caused the site's own JSON-LD
    Organization block to be emitted as a fake "company" ~38 times.
    """
    assert classify_path("/company") == PageCategory.COMPANY
    assert classify_path("/companies") == PageCategory.COMPANIES
    assert classify_path("/companies/acme-inc") == PageCategory.COMPANIES
    assert classify_path("/insights/company-updates-2024") == PageCategory.COMPANY


def test_board_does_not_match_inside_dashboard():
    assert classify_path("/board-of-directors") == PageCategory.BOARD
    assert classify_path("/dashboard") == PageCategory.OTHER


def test_compound_slugs_still_classify():
    assert classify_path("/list-of-members/") == PageCategory.MEMBERS
    assert classify_path("/about-us") == PageCategory.ABOUT
    assert classify_path("/member-directory") == PageCategory.MEMBERS


def test_home_and_root():
    assert classify_path("") == PageCategory.HOME
    assert classify_path("/") == PageCategory.HOME
