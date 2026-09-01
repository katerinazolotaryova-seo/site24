"""Tests the DataForSEO provider against recorded fixture responses — no
network access, no live account, per the plan's testing principle (§3):
"Pipeline correctness must be testable without spending real API budget on
every CI run."
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from analyzer.providers.dataforseo import DataForSEODataProvider

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "dataforseo"


def _load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture()
def provider() -> DataForSEODataProvider:
    p = DataForSEODataProvider(login="test-login", password="test-password")
    yield p
    p.close()


@respx.mock
def test_get_domain_metrics_persists_raw_and_estimates_cost(provider: DataForSEODataProvider):
    fixture = _load_fixture("domain_rank_overview.json")
    route = respx.post("https://api.dataforseo.com/v3/dataforseo_labs/google/domain_rank_overview/live").mock(
        return_value=httpx.Response(200, json=fixture)
    )

    response = provider.get_domain_metrics("acme-roofing.example", country="us", language="en")

    assert route.called
    assert response.provider == "dataforseo"
    assert response.endpoint == "domain_rank_overview"
    assert response.raw_response == fixture
    # base_cost_usd for domain_rank_overview per resources/dataforseo_pricing.yaml
    assert response.estimated_cost_usd == pytest.approx(0.01)


@respx.mock
def test_get_organic_keywords_cost_scales_with_limit(provider: DataForSEODataProvider):
    fixture = _load_fixture("ranked_keywords.json")
    respx.post("https://api.dataforseo.com/v3/dataforseo_labs/google/ranked_keywords/live").mock(
        return_value=httpx.Response(200, json=fixture)
    )

    response = provider.get_organic_keywords("acme-roofing.example", country="us", language="en", limit=500)

    assert response.raw_response["tasks"][0]["result"][0]["items_count"] == 2
    # ranked_keywords: per_row_usd 0.0002 * 500 rows
    assert response.estimated_cost_usd == pytest.approx(0.10)


@respx.mock
def test_get_competitors(provider: DataForSEODataProvider):
    fixture = _load_fixture("competitors_domain.json")
    respx.post("https://api.dataforseo.com/v3/dataforseo_labs/google/competitors_domain/live").mock(
        return_value=httpx.Response(200, json=fixture)
    )

    response = provider.get_competitors("acme-roofing.example", country="us", language="en", limit=5)
    items = response.raw_response["tasks"][0]["result"][0]["items"]
    assert {item["domain"] for item in items} == {"bestlocalroofers.example", "roofprosinc.example"}


@respx.mock
def test_get_serp(provider: DataForSEODataProvider):
    fixture = _load_fixture("serp_organic_live_advanced.json")
    respx.post("https://api.dataforseo.com/v3/serp/google/organic/live/advanced").mock(
        return_value=httpx.Response(200, json=fixture)
    )

    response = provider.get_serp("roof replacement cost", country="us", language="en")
    assert response.endpoint == "serp_organic_live_advanced"
    assert response.raw_response["tasks"][0]["result"][0]["keyword"] == "roof replacement cost"


def test_backlinks_not_implemented_yet(provider: DataForSEODataProvider):
    # Backlink Profile Analyzer is Phase 5 — the method exists (interface
    # compliance) but intentionally isn't wired up yet.
    with pytest.raises(NotImplementedError):
        provider.get_backlinks("acme-roofing.example")

    with pytest.raises(NotImplementedError):
        provider.get_referring_domains("acme-roofing.example")
