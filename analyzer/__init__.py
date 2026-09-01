"""Automated SEO Presale Analyzer.

Internal tool that turns a domain + a few inputs into a presale SEO
analysis: crawl -> SEO data collection -> gap analysis -> opportunity
detection -> LLM interpretation -> presale report + sales talking points.

See docs/seo-presale-analyzer/ARCHITECTURE_AND_MVP_PLAN.md for the full
architecture, MVP scope, and phased roadmap. This package currently
implements Phase 0 (foundations): project scaffolding, the database
schema, the SEODataProvider abstraction, and the API budget guardrail.
Pipeline stages (crawler, analyzers, report generation) land in later
phases per that plan.
"""

__version__ = "0.1.0"
