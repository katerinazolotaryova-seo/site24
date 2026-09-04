"""Apollo.io adapter -- another leg of the contact waterfall (Stage 18),
used mainly as a phone/email/title enrichment fallback after Hunter and the
website crawl have both come up short. Optional and independent.
"""

from __future__ import annotations

from typing import Optional

import httpx

from providers.base import BaseProvider, ProviderError, provider_retry
from src.logging_setup import get_logger

log = get_logger(__name__)

BASE_URL = "https://api.apollo.io/v1"


class ApolloProvider(BaseProvider):
    name = "apollo"

    def __init__(self, api_key: Optional[str], enabled: bool, dry_run: bool, credit_limit: int, rps: float = 1.0):
        super().__init__(enabled=enabled and bool(api_key), dry_run=dry_run, rps=rps, credit_limit=credit_limit)
        self.api_key = api_key

    async def enrich_person(self, full_name: str, domain: str) -> Optional[dict]:
        """Returns a dict with any of email/phone/linkedin_url found, or None."""
        if not self.is_usable():
            return None
        if self.budget and not self._spend(f"person_match:{domain}:{full_name}"):
            return None
        await self.limiter.acquire()
        try:
            data = await self._match_person(full_name, domain)
        except ProviderError as exc:
            log.warning("apollo_enrich_failed", domain=domain, name=full_name, error=str(exc))
            return None
        if not data:
            return None

        out: dict = {}
        email = data.get("email")
        if email and data.get("email_status") == "verified":
            out["email"] = {"email": email, "confidence": 0.85, "provider": "apollo"}
        phone = None
        for phone_obj in data.get("phone_numbers", []) or []:
            if phone_obj.get("status") == "verified":
                phone = phone_obj.get("raw_number")
                break
        if phone:
            out["phone"] = {"phone": phone, "confidence": 0.75, "provider": "apollo"}
        linkedin_url = data.get("linkedin_url")
        if linkedin_url:
            out["linkedin"] = {"linkedin": linkedin_url, "confidence": 0.7, "provider": "apollo"}
        return out or None

    @provider_retry()
    async def _match_person(self, full_name: str, domain: str) -> Optional[dict]:
        parts = full_name.strip().split()
        first, last = (parts[0], " ".join(parts[1:])) if len(parts) >= 2 else (full_name, "")
        payload = {
            "api_key": self.api_key,
            "first_name": first,
            "last_name": last,
            "domain": domain,
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(f"{BASE_URL}/people/match", json=payload)
        except httpx.HTTPError as exc:
            raise ProviderError(str(exc)) from exc
        if resp.status_code >= 500 or resp.status_code == 429:
            raise ProviderError(f"apollo status {resp.status_code}")
        if resp.status_code >= 400:
            log.info("apollo_no_result", domain=domain, status=resp.status_code)
            return None
        return resp.json().get("person")
