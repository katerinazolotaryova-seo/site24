"""AccountQualificationEngine (Stage 16).

Computes:
  1. ICP fit score (0-100) from firmographic + crawl signals.
  2. SEO/PPC opportunity (average of the two dedicated scorers).
  3. Final weighted account_score, using configurable weights from
     config.yaml `qualification.weights`.

This is the gate that decides whether a company is worth spending money on
enrichment for (Stage 17 only runs for account_score >= threshold).
"""

from __future__ import annotations

from dataclasses import dataclass

from src.models import Company, USPresenceStatus
from src.qualification.ppc_score import score_ppc_opportunity
from src.qualification.seo_score import score_seo_opportunity

ICP_WEIGHTS = {
    "us_company_verified": 20,
    "commercial_website": 10,
    "employees_20_plus": 10,
    "employees_50_plus": 5,
    "marketing_department_exists": 10,
    "ecommerce_saas_or_b2b_services": 10,
    "multi_location": 5,
    "multiple_products_or_services": 5,
    "active_hiring": 5,
}

DEFAULT_WEIGHTS = {
    "icp_fit": 0.30,
    "seo_ppc_opportunity": 0.35,
    "ukraine_connection": 0.20,
    "us_verification": 0.10,
    "trigger_intent": 0.05,
}


@dataclass
class AccountScoreResult:
    icp_score: float
    seo_score: float
    ppc_score: float
    seo_ppc_opportunity: float
    ukraine_connection_score: float
    us_verification_score: float
    trigger_intent_score: float
    account_score: float


class AccountQualificationEngine:
    def __init__(self, weights: dict | None = None, min_account_score: float = 65.0):
        self.weights = {**DEFAULT_WEIGHTS, **(weights or {})}
        self.min_account_score = min_account_score

    def score_icp_fit(self, company: Company) -> float:
        signals = company.crawl_signals or {}
        score = 0

        if company.us_presence_status == USPresenceStatus.VERIFIED_US:
            score += ICP_WEIGHTS["us_company_verified"]
        elif company.us_presence_status == USPresenceStatus.PROBABLE_US:
            score += ICP_WEIGHTS["us_company_verified"] * 0.5

        if signals.get("commercial_website", bool(company.website)):
            score += ICP_WEIGHTS["commercial_website"]

        if company.employee_estimate:
            if company.employee_estimate >= 20:
                score += ICP_WEIGHTS["employees_20_plus"]
            if company.employee_estimate >= 50:
                score += ICP_WEIGHTS["employees_50_plus"]

        if signals.get("marketing_department_exists"):
            score += ICP_WEIGHTS["marketing_department_exists"]

        if signals.get("ecommerce_saas_or_b2b_services") or signals.get("is_ecommerce"):
            score += ICP_WEIGHTS["ecommerce_saas_or_b2b_services"]

        if signals.get("multi_location"):
            score += ICP_WEIGHTS["multi_location"]

        if signals.get("multiple_products_or_services"):
            score += ICP_WEIGHTS["multiple_products_or_services"]

        if signals.get("active_hiring"):
            score += ICP_WEIGHTS["active_hiring"]

        return min(100.0, float(score))

    def score_us_verification(self, company: Company) -> float:
        mapping = {
            USPresenceStatus.VERIFIED_US: 100.0,
            USPresenceStatus.PROBABLE_US: 55.0,
            USPresenceStatus.UNKNOWN: 15.0,
            USPresenceStatus.NOT_US: 0.0,
        }
        return mapping.get(company.us_presence_status, 0.0)

    def score_trigger_intent(self, company: Company) -> float:
        signals = company.crawl_signals or {}
        score = 0.0
        if signals.get("active_hiring"):
            score += 60.0
        if signals.get("recent_funding") or signals.get("recent_press"):
            score += 40.0
        return min(100.0, score)

    def score_ukraine_connection(self, best_person_score: float) -> float:
        return max(0.0, min(100.0, best_person_score))

    def score(self, company: Company, best_ukraine_connection_score: float = 0.0) -> AccountScoreResult:
        icp = self.score_icp_fit(company)
        seo = float(company.seo_score) if company.seo_score else float(score_seo_opportunity(company))
        ppc = float(company.ppc_score) if company.ppc_score else float(score_ppc_opportunity(company))
        seo_ppc = (seo + ppc) / 2.0
        ukraine = self.score_ukraine_connection(best_ukraine_connection_score)
        us_verification = self.score_us_verification(company)
        trigger = self.score_trigger_intent(company)

        final = (
            icp * self.weights["icp_fit"]
            + seo_ppc * self.weights["seo_ppc_opportunity"]
            + ukraine * self.weights["ukraine_connection"]
            + us_verification * self.weights["us_verification"]
            + trigger * self.weights["trigger_intent"]
        )

        return AccountScoreResult(
            icp_score=round(icp, 2),
            seo_score=round(seo, 2),
            ppc_score=round(ppc, 2),
            seo_ppc_opportunity=round(seo_ppc, 2),
            ukraine_connection_score=round(ukraine, 2),
            us_verification_score=round(us_verification, 2),
            trigger_intent_score=round(trigger, 2),
            account_score=round(final, 2),
        )

    def qualifies(self, result: AccountScoreResult) -> bool:
        return result.account_score >= self.min_account_score
