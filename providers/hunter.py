"""Hunter.io adapter (email finder/verifier) -- one leg of the contact
waterfall (Stage 18). Optional and independent: if disabled or no API key,
`find_email` just returns None so the waterfall falls through to the next
provider.
"""

from __future__ import annotations

from typing import Optional

import httpx

from providers.base import BaseProvider, ProviderError, provider_retry
from src.logging_setup import get_logger

log = get_logger(__name__)

BASE_URL = "https://api.hunter.io/v2"


class HunterProvider(BaseProvider):
    name = "hunter"

    def __init__(self, api_key: Optional[str], enabled: bool, dry_run: bool, credit_limit: int, rps: float = 1.0):
        super().__init__(enabled=enabled and bool(api_key), dry_run=dry_run, rps=rps, credit_limit=credit_limit)
        self.api_key = api_key

    async def find_email(self, domain: str, full_name: str) -> Optional[dict]:
        """Returns {"email": ..., "confidence": 0-1, "provider": "hunter"} or None."""
        if not self.is_usable():
            return None
        if self.budget and not self._spend(f"email_finder:{domain}:{full_name}"):
            return None
        await self.limiter.acquire()
        try:
            parts = full_name.strip().split()
            first, last = (parts[0], parts[-1]) if len(parts) >= 2 else (full_name, "")
            data = await self._email_finder(domain, first, last)
        except ProviderError as exc:
            log.warning("hunter_email_finder_failed", domain=domain, name=full_name, error=str(exc))
            return None
        if not data:
            return None
        email = data.get("email")
        if not email:
            return None
        score = data.get("score", 0) or 0
        return {"email": email, "confidence": round(score / 100.0, 2), "provider": "hunter"}

    @provider_retry()
    async def _email_finder(self, domain: str, first_name: str, last_name: str) -> Optional[dict]:
        params = {
            "domain": domain,
            "first_name": first_name,
            "last_name": last_name,
            "api_key": self.api_key,
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(f"{BASE_URL}/email-finder", params=params)
        except httpx.HTTPError as exc:
            raise ProviderError(str(exc)) from exc
        if resp.status_code >= 500 or resp.status_code == 429:
            raise ProviderError(f"hunter status {resp.status_code}")
        if resp.status_code >= 400:
            log.info("hunter_no_result", domain=domain, status=resp.status_code)
            return None
        return resp.json().get("data")
