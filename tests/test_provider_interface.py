from __future__ import annotations

from datetime import UTC, datetime

import pytest

from analyzer.providers.base import RawProviderResponse, SEODataProvider


def test_seo_data_provider_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        SEODataProvider()  # abstract — must be subclassed


class _FakeProvider(SEODataProvider):
    """Minimal concrete implementation, to prove the interface is satisfiable
    without depending on any real vendor — this is what a future Ahrefs/Semrush
    adapter (or a test double for pipeline tests) looks like."""

    def _fake_response(self, endpoint: str) -> RawProviderResponse:
        return RawProviderResponse(
            provider="fake",
            endpoint=endpoint,
            request_params={},
            raw_response={},
            estimated_cost_usd=0.0,
            fetched_at=datetime.now(UTC),
        )

    def get_domain_metrics(self, domain, *, country, language):
        return self._fake_response("get_domain_metrics")

    def get_organic_keywords(self, domain, *, country, language, limit=500):
        return self._fake_response("get_organic_keywords")

    def get_top_pages(self, domain, *, country, language, limit=100):
        return self._fake_response("get_top_pages")

    def get_competitors(self, domain, *, country, language, limit=10):
        return self._fake_response("get_competitors")

    def get_backlinks(self, domain, *, limit=100):
        return self._fake_response("get_backlinks")

    def get_referring_domains(self, domain, *, limit=100):
        return self._fake_response("get_referring_domains")

    def get_keyword_metrics(self, keywords, *, country, language):
        return self._fake_response("get_keyword_metrics")

    def get_serp(self, keyword, *, country, language, depth=10):
        return self._fake_response("get_serp")


def test_fake_provider_satisfies_the_full_interface():
    provider = _FakeProvider()
    domain_metrics = provider.get_domain_metrics("x.example", country="us", language="en")
    assert domain_metrics.endpoint == "get_domain_metrics"
    assert provider.get_serp("kw", country="us", language="en").provider == "fake"
