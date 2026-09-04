"""USCompanyVerifier (Stage 12).

Classifies whether a company genuinely operates in the US, from public
signals collected during discovery/crawl -- never assumed just because a
person "looks" US-based.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models import Evidence, USPresenceStatus

US_STATE_NAMES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut",
    "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan",
    "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york", "north carolina",
    "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania", "rhode island",
    "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont",
    "virginia", "washington", "west virginia", "wisconsin", "wyoming",
    "district of columbia",
}

# Signal name -> points. See Stage 12 "сильные сигналы".
SIGNAL_WEIGHTS = {
    "hq_in_usa": 40,
    "us_office": 25,
    "us_corporate_address": 25,
    "linkedin_country_us": 30,
    "website_lists_us_location": 20,
    "us_incorporation": 25,
    "main_operating_market_usa": 20,
    "us_state_in_address": 20,
    "us_phone_number": 10,
}


@dataclass
class USCompanySignals:
    hq_in_usa: bool = False
    us_office: bool = False
    us_corporate_address: bool = False
    linkedin_country_us: bool = False
    website_lists_us_location: bool = False
    us_incorporation: bool = False
    main_operating_market_usa: bool = False
    us_state_in_address: bool = False
    us_phone_number: bool = False
    evidence: list[Evidence] = field(default_factory=list)

    def active_signals(self) -> list[str]:
        return [name for name in SIGNAL_WEIGHTS if getattr(self, name, False)]

    def score(self) -> int:
        return min(100, sum(SIGNAL_WEIGHTS[name] for name in self.active_signals()))


class USCompanyVerifier:
    def __init__(self, verified_threshold: int = 60, probable_threshold: int = 30):
        self.verified_threshold = verified_threshold
        self.probable_threshold = probable_threshold

    def signals_from_address(self, city: str | None, state: str | None, address_text: str | None) -> USCompanySignals:
        signals = USCompanySignals()
        if state and state.strip().lower() in US_STATE_NAMES:
            signals.us_state_in_address = True
        if address_text:
            lowered = address_text.lower()
            if any(s in lowered for s in US_STATE_NAMES) or "usa" in lowered or "united states" in lowered:
                signals.us_corporate_address = True
        return signals

    def signals_from_crawl_signals(self, crawl_signals: dict | None) -> USCompanySignals:
        """Picks up any of the SIGNAL_WEIGHTS booleans that discovery/crawl
        stages already deposited directly into Company.crawl_signals (e.g.
        a company-website crawl that found "Headquartered in the United
        States", or a LinkedIn company page fetch that read country=US).
        """
        signals = USCompanySignals()
        for name in SIGNAL_WEIGHTS:
            if crawl_signals and crawl_signals.get(name):
                setattr(signals, name, True)
        return signals

    def verify(self, signals: USCompanySignals) -> tuple[USPresenceStatus, int]:
        score = signals.score()
        if score >= self.verified_threshold:
            return USPresenceStatus.VERIFIED_US, score
        if score >= self.probable_threshold:
            return USPresenceStatus.PROBABLE_US, score
        if score == 0:
            return USPresenceStatus.UNKNOWN, score
        return USPresenceStatus.UNKNOWN, score

    def merge_signals(self, *signal_sets: USCompanySignals) -> USCompanySignals:
        merged = USCompanySignals()
        for s in signal_sets:
            for name in SIGNAL_WEIGHTS:
                if getattr(s, name, False):
                    setattr(merged, name, True)
            merged.evidence.extend(s.evidence)
        return merged
