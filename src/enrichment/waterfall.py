"""Contact enrichment waterfall (Stage 17 + 18).

Order: official company website -> public person website/profile (already
folded into the crawl step) -> search engine (not separately implemented --
covered by discovery) -> Hunter API -> Apollo API -> other configurable
provider.

Cost controls:
  * Only called for companies with account_score >= qualification threshold
    (enforced by the orchestrator before this module is even invoked).
  * Only targets priority roles, chosen by company size band
    (config.yaml `enrichment.roles_by_company_size`).
  * Skips a field once it already has confidence >= configured threshold.
  * Caps enriched people per company (`max_people_per_company`).
"""

from __future__ import annotations

from dataclasses import dataclass

from providers.apollo import ApolloProvider
from providers.hunter import HunterProvider
from src.crawling.website_crawler import CrawlResult
from src.enrichment.email import email_from_crawl, email_from_hunter
from src.enrichment.phone import phone_from_apollo, phone_from_crawl
from src.enrichment.social import socials_from_apollo_result, socials_from_crawl
from src.logging_setup import get_logger
from src.models import Company, FieldValue, NormalizedRole, Person

log = get_logger(__name__)


@dataclass
class SizeBand:
    max_employees: int | None
    roles: list[str]


_VALID_ROLE_VALUES = {r.value for r in NormalizedRole}


def select_priority_roles(company: Company, roles_by_size: dict) -> list[NormalizedRole]:
    employees = company.employee_estimate or 0
    bands = [
        ("small", roles_by_size.get("small", {})),
        ("medium", roles_by_size.get("medium", {})),
        ("large", roles_by_size.get("large", {})),
    ]
    for _, band in bands:
        max_emp = band.get("max_employees")
        if max_emp is None or employees < max_emp:
            return [NormalizedRole(r) for r in band.get("roles", []) if r in _VALID_ROLE_VALUES]
    large = roles_by_size.get("large", {})
    return [NormalizedRole(r) for r in large.get("roles", []) if r in _VALID_ROLE_VALUES]


def select_people_to_enrich(
    people: list[Person],
    company: Company,
    roles_by_size: dict,
    max_people_per_company: int = 5,
) -> list[Person]:
    priority_roles = select_priority_roles(company, roles_by_size)
    candidates = [p for p in people if p.normalized_role in priority_roles]
    # founders/CEO first, then marketing DMs, preserving relative order
    candidates.sort(key=lambda p: priority_roles.index(p.normalized_role) if p.normalized_role in priority_roles else 999)
    return candidates[:max_people_per_company]


class ContactWaterfall:
    def __init__(
        self,
        hunter: HunterProvider | None = None,
        apollo: ApolloProvider | None = None,
        skip_email_if_confidence_gte: float = 0.90,
        skip_phone_if_confidence_gte: float = 0.90,
    ):
        self.hunter = hunter
        self.apollo = apollo
        self.skip_email_if_confidence_gte = skip_email_if_confidence_gte
        self.skip_phone_if_confidence_gte = skip_phone_if_confidence_gte

    async def enrich_person(self, person: Person, crawl: CrawlResult | None) -> Person:
        # --- email --------------------------------------------------------
        if not (person.email and person.email.confidence >= self.skip_email_if_confidence_gte):
            found = email_from_crawl(person.full_name, crawl)
            if found is None and self.hunter is not None and person.company_domain:
                found = await email_from_hunter(self.hunter, person.company_domain, person.full_name)
            if found is not None:
                person.email = found

        # --- socials --------------------------------------------------------
        crawl_socials = socials_from_crawl(crawl)
        for platform, value in crawl_socials.items():
            if getattr(person, platform) is None:
                setattr(person, platform, value)

        # --- phone ----------------------------------------------------------
        if not (person.phone and person.phone.confidence >= self.skip_phone_if_confidence_gte):
            found = phone_from_crawl(crawl)
            if found is None and self.apollo is not None and person.company_domain:
                found = await phone_from_apollo(self.apollo, person.full_name, person.company_domain)
            if found is not None:
                person.phone = found

        # --- apollo fallback for linkedin / anything still missing --------
        if self.apollo is not None and person.company_domain and (person.linkedin is None or person.email is None):
            apollo_result = await self.apollo.enrich_person(person.full_name, person.company_domain)
            for platform, value in socials_from_apollo_result(apollo_result).items():
                if getattr(person, platform) is None:
                    setattr(person, platform, value)
            if person.email is None and apollo_result and "email" in apollo_result:
                data = apollo_result["email"]
                person.email = FieldValue(value=data["email"], confidence=data["confidence"], provider="apollo")

        return person

    def has_usable_contact_channel(self, person: Person) -> bool:
        return any([person.linkedin, person.email, person.phone, person.telegram, person.instagram, person.facebook])

    async def enrich_company_people(
        self,
        people: list[Person],
        company: Company,
        crawl: CrawlResult | None,
        roles_by_size: dict,
        max_people_per_company: int = 5,
    ) -> list[Person]:
        targets = select_people_to_enrich(people, company, roles_by_size, max_people_per_company)
        enriched_ids = set()
        for person in targets:
            await self.enrich_person(person, crawl)
            enriched_ids.add(person.person_id)
            if self.has_usable_contact_channel(person):
                log.info("usable_contact_found", person=person.full_name, company=company.company_name)
        return people
