"""Shared provider infrastructure: rate limiting, retry/backoff, credit
budgets, and a common result envelope so every external integration
(search, Hunter, Apollo, ...) behaves consistently and cheaply.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.logging_setup import get_logger

log = get_logger(__name__)


class ProviderError(Exception):
    """Raised for retryable provider failures (network/5xx/429)."""


class CreditLimitExceeded(Exception):
    """Raised when a provider's configured monthly/run credit budget is spent."""


class RateLimiter:
    """A simple token-bucket-ish limiter: at most `rps` calls per second,
    shared across all callers via an asyncio lock. Good enough for the
    volumes this system needs (single-digit to low tens of RPS).
    """

    def __init__(self, rps: float):
        self.min_interval = 1.0 / rps if rps > 0 else 0.0
        self._lock = asyncio.Lock()
        self._last_call = 0.0

    async def acquire(self) -> None:
        if self.min_interval <= 0:
            return
        async with self._lock:
            now = time.monotonic()
            wait = self._last_call + self.min_interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()


@dataclass
class CreditBudget:
    """Tracks provider "credits" (API calls) spent within a run so we never
    blow through a paid quota by accident (Stage: "provider credit limits").
    """

    limit: int
    spent: int = 0
    ledger: list[str] = field(default_factory=list)

    def can_spend(self, n: int = 1) -> bool:
        return self.spent + n <= self.limit

    def spend(self, reason: str, n: int = 1) -> None:
        if not self.can_spend(n):
            raise CreditLimitExceeded(f"budget of {self.limit} exhausted (attempted +{n} for {reason})")
        self.spent += n
        self.ledger.append(reason)

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.spent)


def provider_retry(max_attempts: int = 3):
    """Standard retry/backoff decorator for provider HTTP calls."""

    return retry(
        reraise=True,
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        retry=retry_if_exception_type(ProviderError),
    )


@dataclass
class ProviderResult:
    ok: bool
    data: Any = None
    error: Optional[str] = None
    from_cache: bool = False
    dry_run: bool = False


class BaseProvider:
    """Common lifecycle for a provider: enabled flag, dry-run awareness,
    rate limiting and a credit budget. Subclasses implement `_call`.
    """

    name = "base"

    def __init__(
        self,
        enabled: bool = False,
        dry_run: bool = True,
        rps: float = 1.0,
        credit_limit: int = 0,
    ):
        self.enabled = enabled
        self.dry_run = dry_run
        self.limiter = RateLimiter(rps)
        self.budget = CreditBudget(limit=credit_limit) if credit_limit else None

    def is_usable(self) -> bool:
        return self.enabled and not self.dry_run

    def _spend(self, reason: str) -> bool:
        if self.budget is None:
            return True
        try:
            self.budget.spend(reason)
            return True
        except CreditLimitExceeded:
            log.warning("provider_credit_limit_exceeded", provider=self.name, reason=reason)
            return False
