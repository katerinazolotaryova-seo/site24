# SEO Presale Analyzer

Internal tool for automated SEO presale analysis. Full architecture, MVP
scope, and phased roadmap: [`docs/seo-presale-analyzer/ARCHITECTURE_AND_MVP_PLAN.md`](docs/seo-presale-analyzer/ARCHITECTURE_AND_MVP_PLAN.md).

**Status:** Phase 0 (foundations) — project scaffolding, database schema,
the `SEODataProvider` abstraction, and the API budget guardrail. The crawler
and analysis pipeline (Phase 1+) aren't built yet.

Before pointing anything in here at a real prospect's or competitor's
domain, see [`docs/seo-presale-analyzer/LEGAL_SIGNOFF.md`](docs/seo-presale-analyzer/LEGAL_SIGNOFF.md) — it must be filled in and approved first.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env   # fill in DataForSEO / Anthropic credentials when you have them

docker compose up -d   # Postgres + Redis
python -m analyzer init-db
```

Without `docker compose`/a configured `.env`, `ANALYZER_DATABASE_URL`
defaults to a local SQLite file (`analyzer_dev.db`), which is enough to run
`init-db` and the test suite.

## CLI

```bash
python -m analyzer --help
python -m analyzer version
python -m analyzer init-db          # alembic upgrade head
python -m analyzer estimate-cost    # pre-flight DataForSEO cost estimate vs. the $8 default budget
```

## Tests

```bash
pytest
```

Provider tests run against recorded fixture responses
(`tests/fixtures/dataforseo/`) — no live DataForSEO account or network
access is needed or used.

## Layout

```
analyzer/
  config.py            # env-driven settings (ANALYZER_* variables)
  cli.py                # CLI entrypoint (python -m analyzer)
  db/
    models.py           # ORM models — the MVP schema (plan §6)
    migrations/          # Alembic
  providers/
    base.py              # SEODataProvider interface (plan §23)
    dataforseo.py         # DataForSEO implementation
    gateway.py             # budget check + persistence wrapper — pipeline code
                            # always calls providers through this, never directly
  budget/
    estimator.py          # pre-flight cost estimation
    tracker.py             # per-project running spend + enforcement
  resources/
    dataforseo_pricing.yaml  # planning-level cost table (verify before production use)
```
