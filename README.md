# Ukraine-US Leads

Discovers US-based companies whose **Founder/Owner/CEO** or **marketing
decision-maker** (CMO, VP Marketing, Head of Marketing, Marketing Director,
Head of Growth, Head of Digital) has a **publicly, professionally
documented** connection to Ukraine — then qualifies those companies for
SEO/PPC outreach and, only for the accounts worth the spend, enriches
contact details.

**Never** infers a Ukraine connection from a name, surname, language,
photo, school, or employer alone. Every `verified`/`probable` classification
in `people.csv` traces back to a specific public source URL and evidence
type — see [Ukraine-connection verification](#ukraine-connection-verification).

## How it works

Two independent, converging pipelines feed one qualification/enrichment
funnel:

- **Pipeline A — Company → Person.** Ukrainian-American business
  directories, chambers of commerce, communities, conferences and general
  web search surface US companies; the company's own site and further
  search then surface its founders and marketing decision-makers.
- **Pipeline B — Person → Company.** Search targets Ukraine-connected
  marketers/founders directly (plus alumni of well-known Ukrainian tech
  companies, used only as a *discovery signal*, never as proof); their
  current US employer is then resolved.

```
DISCOVER SOURCES → DISCOVER PEOPLE/COMPANIES → NORMALIZE → DEDUPLICATE
   → VERIFY UKRAINE CONNECTION → VERIFY US COMPANY → CRAWL COMPANY WEBSITE
   → IDENTIFY FOUNDER/MARKETING DM → ACCOUNT QUALIFICATION → SEO/PPC SCORE
   → FILTER LOW-VALUE ACCOUNTS → CONTACT ENRICHMENT → CONTACT CONFIDENCE
   → MANUAL REVIEW → EXPORT
```

See `src/orchestrator.py` for the exact stage wiring — it's a literal,
1:1 implementation of that diagram.

Cost discipline is a first-class design goal, not an afterthought: paid
contact-enrichment (Hunter/Apollo) only ever runs *after* an account has
already cleared `qualification.min_account_score`, and only for that
company's priority decision-maker roles (see `enrichment.roles_by_company_size`
in `config/config.yaml`). A funnel that starts at 10,000 discovered records
should reach paid enrichment for only a few hundred.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in whatever API keys you actually have; every
                        # integration is optional and degrades gracefully

# Dry-run (default): no network calls to search/enrichment providers,
# safe to run anywhere. Loads config/seed_sources.csv and exercises the
# full pipeline end to end (produces empty-but-correctly-shaped CSVs
# unless you've supplied real seed sources or provider keys).
python main.py

# Small validation run against real providers (once configured in .env):
python main.py --live --max-records 100

# Force dry-run regardless of .env:
python main.py --dry-run

# Clear checkpoints and start over:
python main.py --reset
```

Output lands in `output/`:

```
output/
    companies.csv
    people.csv
    qualified_accounts.csv
    manual_review.csv
    sources.csv
    discovery_log.jsonl
```

## Configuration

Everything lives in `config/`:

| File | Purpose |
|---|---|
| `config.yaml` | Master config — discovery toggles, crawler limits, scoring weights, qualification thresholds, provider enable flags. All qualification weights are configurable (`qualification.weights`). |
| `roles.yaml` | Job-title → `normalized_role` patterns, and which roles are enrichment priorities per company-size band. |
| `states.yaml` | All 50 US states + DC, for Stage 3 state-level search. |
| `cities.yaml` | Configurable major-city list for Stage 4 city-level search. |
| `seed_sources.csv` | Seed Ukrainian-American business directories/associations/communities (`source_name,source_url,source_type`). **Replace the placeholder `example.org` rows with real, vetted directory URLs before a production run** — they're left as placeholders deliberately rather than guessed real organization URLs. |
| `ukraine_companies.yaml` | Known Ukrainian-tech/business-ecosystem companies (Genesis, MacPaw, Grammarly, ...) — a *discovery signal only* (Stage 10), never evidence of anyone's nationality. |

Secrets and runtime toggles come from `.env` (see `.env.example`): search
backend + API key, Hunter/Apollo keys and credit limits, `DRY_RUN`, log
level, cache/checkpoint directories.

### `dry_run`

`DRY_RUN=true` (the default) makes every provider (`SearchProvider`,
`WebsiteCrawler`/`PageFetcher`, `HunterProvider`, `ApolloProvider`) a
no-op — nothing touches the network. This is what makes the pipeline safe
to run in CI, in a sandboxed environment, or before you've configured any
provider keys: it exercises 100% of the normalize → dedupe → verify →
qualify → manual-review → export logic against whatever you seed directly,
and the discovery stages just come back empty. Flip it off (`--live`, or
`DRY_RUN=false` in `.env`) once you've configured a search backend.

## Architecture

```
config/            YAML + CSV configuration (see table above)
src/
  models.py         Pydantic models: Company, Person, Evidence, DiscoverySource, ...
  config.py         AppConfig loader (config.yaml + .env)
  logging_setup.py  Structured JSON logging (structlog, with a stdlib fallback)
  cache.py          On-disk request cache (sharded JSON files, TTL)
  checkpoint.py     Checkpoint/resume markers per pipeline stage
  orchestrator.py   Stage 21 pipeline wiring

  discovery/        Stages 1-10: seed ingestion, community/event discovery,
                     state/city web search, founder + marketing-DM discovery,
                     person->company discovery, Ukraine-company-alumni signal
  crawling/          Stage 13: targeted website crawler, page classifier,
                     JSON-LD/schema.org + mailto/tel/social-link parser
  verification/      Stages 11-14: UkraineConnectionVerifier, USCompanyVerifier,
                     PersonMatcher, CompanyMatcher
  processing/        normalizer, deduplicator (Stage 15), role_classifier
  qualification/      Stage 16: AccountQualificationEngine, SEO/PPC opportunity scorers
  enrichment/         Stages 17-18: email/phone/social waterfall with confidence-gated skips
  exporters/          CSV + discovery_log.jsonl writers

providers/           Pluggable, optional, independent integrations:
                     search_provider (SerpApi/Google CSE/Bing), hunter, apollo
tests/               pytest suite (see below)
main.py              CLI entrypoint
```

## Ukraine-connection verification

`src/verification/ukraine_connection.py` implements Stage 11 exactly as
specified:

- **Evidence, not inference.** A page has to actually describe *this
  specific person* (name-anchored, or a short single-subject bio) using a
  self-identification phrase ("Ukrainian entrepreneur", "founder from
  Ukraine", "born in Ukraine", ...) or a credible professional bio/
  interview/conference-speaker page to count as evidence at all.
- **A search-snippet mention of "Ukraine" is never evidence.** Every
  discovery module that finds a person via search (`founder_discovery`,
  `marketer_discovery`) fetches and reads the actual page before calling
  `extract_evidence` — never the search snippet.
- **Discovery signals ≠ evidence.** A Slavic-looking surname, having worked
  at a well-known Ukrainian company (`ukraine_companies.yaml`), or
  following Ukrainian community pages are recorded as
  `DISCOVERY_SIGNAL_*` evidence with `confidence=0.0` — structurally
  incapable of raising the score (`NON_EVIDENCE_TYPES` is enforced in
  `UkraineConnectionVerifier.score_evidence`). They only justify queuing a
  candidate for further, real verification.
- **Scoring** follows the spec's rubric (self-identification=100,
  official/professional bio=90/80, conference bio=85, two independent
  professional sources ⇒ floor of 75, etc.) and maps to
  `verified` (≥85) / `probable` (65-84) / `manual_review` (40-64) /
  `unknown` (<40). The default outbound list (`qualification.outbound_statuses`
  in `config.yaml`) only includes `verified`; add `probable` to widen it.

## Testing / validation

```bash
python -m pytest -q
```

The suite (`tests/`) covers:

- `test_ukraine_connection.py` — self-identification extraction, the
  "discovery signal alone never scores" guarantee, the two-independent-
  sources floor, and that a bare snippet mention never counts.
- `test_person_matcher.py` / `test_company_matcher.py` — identity
  resolution, including the "two John Smiths at different companies"
  false-merge case.
- `test_role_classifier.py`, `test_normalizer.py` — title/name/domain/phone
  normalization.
- `test_extraction_utils.py`, `test_founder_marketer_discovery.py` — page
  parsing (JSON-LD `Person`/`Organization`, heading-pattern extraction) and
  founder/marketing-DM discovery end to end against stubbed search+fetch
  layers (no real network).
- `test_account_score.py` — ICP/SEO/PPC/Ukraine-connection weighting,
  including that the weights are genuinely configurable.
- `test_orchestrator_dryrun.py` — the full NORMALIZE → ... → EXPORT half of
  the pipeline against seeded synthetic companies/people, asserting the
  produced `qualified_accounts.csv`/`people.csv` rows and the manual-review
  routing for ambiguous Ukraine-connection evidence.

### Recommended rollout (per the spec's Phase 5)

Don't point this at "discover everything" on day one. Validate on ~50-100
discovered companies first (`--max-records 100`, or a short seed file +
`discovery.states`/`discovery.cities` narrowed to 2-3 entries in
`config.yaml`) and measure, from `people.csv` + `manual_review.csv`:

- Ukraine-connection precision (spot-check the `verified` rows' source URLs)
- person-matching accuracy (spot-check `manual_review.csv` "duplicate
  conflict" rows)
- duplicate rate (`sources.csv` vs. distinct domains in `companies.csv`)
- US-company verification accuracy (`us_presence_status` vs. reality)
- % of qualified companies with a usable decision-maker
  (`qualified_accounts.csv` `qualifying_person_*` columns)
- % with a usable contact channel (`qualifying_person_contact_channel != "none"`)
- API cost per qualified account (Hunter/Apollo credit ledgers, see
  `providers/base.py` `CreditBudget`)

Only widen `discovery.*` scope and provider credit limits once those numbers
look right. The target is precision — a small list of real, verifiable,
commercially-promising accounts — not maximum row count.

## Privacy / safety

- Only public, professional sources: business directories, chamber/
  association pages, conference/speaker pages, company "About"/leadership
  pages, public LinkedIn search results, and approved enrichment APIs
  (Hunter, Apollo).
- No ethnicity/nationality inference from names, photos, or language. No
  CAPTCHA/auth bypass, no private-profile scraping, no leaked databases, no
  private/hidden APIs.
- Every Ukraine-connection classification carries an explicit
  `source_url` + `evidence_type` (see `Evidence`/`UkraineConnection` in
  `src/models.py`) and a short (<240 char) fragment — never a full quote.
