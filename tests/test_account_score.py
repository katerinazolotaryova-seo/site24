from src.models import Company, USPresenceStatus
from src.qualification.account_score import AccountQualificationEngine


def test_strong_account_scores_high():
    company = Company(
        company_name="Acme Digital",
        website="https://acme.com",
        domain="acme.com",
        employee_estimate=75,
        us_presence_status=USPresenceStatus.VERIFIED_US,
        crawl_signals={
            "commercial_website": True,
            "marketing_department_exists": True,
            "is_ecommerce": True,
            "multi_location": True,
            "multiple_products_or_services": True,
            "active_hiring": True,
            "has_category_structure": True,
            "has_blog": True,
            "has_google_ads_tag": True,
            "has_conversion_tracking": True,
            "commercial_intent": True,
        },
    )
    engine = AccountQualificationEngine(min_account_score=65)
    result = engine.score(company, best_ukraine_connection_score=95)
    assert result.account_score >= 65
    assert engine.qualifies(result)


def test_weak_account_scores_low():
    company = Company(company_name="Tiny Shop", us_presence_status=USPresenceStatus.UNKNOWN)
    engine = AccountQualificationEngine(min_account_score=65)
    result = engine.score(company, best_ukraine_connection_score=0)
    assert result.account_score < 65
    assert not engine.qualifies(result)


def test_weights_are_configurable():
    company = Company(company_name="X", us_presence_status=USPresenceStatus.VERIFIED_US)
    engine_default = AccountQualificationEngine()
    engine_ukraine_heavy = AccountQualificationEngine(weights={"ukraine_connection": 0.9, "icp_fit": 0.025, "seo_ppc_opportunity": 0.025, "us_verification": 0.025, "trigger_intent": 0.025})
    r1 = engine_default.score(company, best_ukraine_connection_score=100)
    r2 = engine_ukraine_heavy.score(company, best_ukraine_connection_score=100)
    assert r2.account_score > r1.account_score
