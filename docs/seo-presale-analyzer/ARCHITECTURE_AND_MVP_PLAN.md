# Automated SEO Presale Analyzer — Architecture & MVP Plan

Status: **DRAFT — for review, not yet approved for implementation.**
Per the brief (§26), this document stops at the planning stage. No pipeline code should be written until the open decisions in §10 are resolved and this plan is signed off.

**Decisions resolved so far** (§10): provider = DataForSEO, per-project API budget = **$8**, output format = **plain text**. See §10 for what remains open, most importantly the legal/compliance sign-off (§10.5, template provided in §12).

---

## 1. Reading of the brief — spory / technically hard spots

Before proposing architecture, these are the points in the brief that are either underspecified, expensive, or risky enough to shape the design decisions below.

| # | Issue | Why it's hard | Design consequence |
|---|---|---|---|
| 1 | **Semantic block detection on pages** (§10) — "not HTML selectors, semantically determine block purpose" | There is no reliable non-LLM way to say "this div is a Testimonials block" across arbitrary site templates. Doing this with an LLM for every client + 3–5 competitor pages × N priority pages is a real cost and latency item, and needs a stable, versioned taxonomy so runs are comparable over time. | Page Structure Analyzer runs as: (a) DOM segmentation into candidate blocks (heading-anchored sections), (b) a single structured-output LLM call per page classifying each candidate block against the fixed taxonomy in §10, with confidence. Cache per URL+content-hash so re-runs don't re-pay for unchanged pages. |
| 2 | **Competitor Discovery via SERP intersection** (§7) | Requires many SERP lookups (one per commercial keyword) before you even know who the competitors are — this is the single most expensive discovery step, and "regularly in TOP-10" needs a keyword *sample*, not the full semantic core, to stay affordable. | Discovery runs SERP calls only for the client's top N commercial-intent keywords (config, default 20–30, prioritized by volume), not the whole keyword set. Exclude-list (Wikipedia, Reddit, YouTube, marketplaces/aggregators) is a maintained config table, not hardcoded, since "aggregator vs. real competitor" is business-type dependent (e.g. Amazon is noise for a services site but a real competitor for some ecommerce niches). |
| 3 | **Intent classification & clustering** (§6) | Provider intent labels (when available) are approximate; volume-based clustering with no ground truth risks noisy clusters. Fully semantic (embedding) clustering adds a new external dependency (embeddings model) and a new tunable (distance threshold) that will need calibration per language. | MVP uses a cheap heuristic (head-term + provider intent flag where available) and defers embedding-based clustering to Phase 3+ once there's a labeled sample to validate against. Every cluster carries its assignment *method* so quality can be audited. |
| 4 | **JS rendering** (§4, §12) | Headless rendering (Playwright) multiplies crawl time/cost and infra footprint. Not all client sites need it. | Crawler is HTTP-first; it renders with Playwright only for URLs where the static response looks anomalously thin relative to page type (e.g. a "service" page under some word-count floor) or where an SPA shell is detected. This is a budget knob, not an always-on cost. |
| 5 | **Cost control on paid SEO data** | DataForSEO/Ahrefs/Semrush all bill per lookup; keyword sets for a domain + 5 competitors can run into the tens of thousands of rows if pulled naively. | Every provider call is (a) capped by a per-project budget config, (b) cached with a freshness window (raw responses keyed by domain+endpoint+params+date), so re-running analysis/report generation never re-purchases data inside that window. This is why raw vs. normalized storage (§24) is mandatory, not a nice-to-have. |
| 6 | **Full-site facts** (orphan pages, true page depth) | Both require a *complete* crawl graph; a budget-limited crawl (which MVP needs, for cost/time reasons) will under-report these. | These are explicitly marked "requires full crawl" and reported with a caveat/confidence flag when the crawl was budget-capped, rather than silently presented as ground truth. |
| 7 | **E-E-A-T is not a score** (§14) | The brief is explicit that this must not become a fake "63/100" number, but "compare presence/absence of trust signals vs competitors" is still a judgment call the LLM makes over crawled content — a hallucination risk area. | E-E-A-T Analyzer produces boolean/enum presence flags per signal (found/not found/unclear) with the evidence URL attached, extracted by a constrained-output LLM pass over already-crawled page content (never free-form). The LLM interpretation layer is only allowed to talk about *gaps in these flags*, never invent a score. |
| 8 | **Anti-hallucination guarantee** (§18) | "LLM must not invent metrics/positions/volumes/problems" is a hard requirement, not a prompting nicety — it needs enforcement, not just instruction. | A **grounding validator** runs on every LLM output before it's accepted: every number in the LLM's text is extracted and checked against the structured input object; anything untraceable fails the pass and triggers regeneration (bounded retries) or falls back to a templated sentence. This is a concrete Phase 7 component, not just a system prompt. |
| 9 | **Scraping competitor pages** (§10) | Fetching competitor sites at volume raises robots.txt/ToS questions, separate from the SEO-data-provider APIs. | Crawl only the specific priority-page URLs identified via SERP (a handful per project, not a competitor-wide crawl), respect robots.txt/crawl-delay, identify with a clear UA string, and keep volume low enough that this is defensible as manual-equivalent research rather than scraping at scale. This should still get an explicit legal/compliance sign-off (see §10 decisions). |
| 10 | **Ecommerce faceted navigation** (§11) | Facet URL combinations are a classic crawl trap (near-infinite URL space). | Crawler enforces URL pattern dedup + a max-facet-depth budget; faceted analysis works off a sampled set of filter combinations, not full enumeration. |
| 11 | **Configurable scoring formula ≠ ground truth** (§17) | Impact/Confidence/Effort/Business relevance are all populated by *rules per opportunity type*, which are themselves subjective first-pass estimates. | Ship the formula and the per-type scoring rules as an explicit, versioned config (not embedded in code), and treat v1 weights as "best guess, to be recalibrated" — flag this to the user now as a decision, not a fact to discover later. |
| 12 | **Provenance on every claim** (§25) | Retrofitting "where did this number come from" onto a pipeline built without it is expensive. It has to be a first-class field from the very first table, not an afterthought. | Every normalized/calculated record carries `source_provider`, `source_endpoint_or_module`, `fetched_at`/`computed_at`, and (where applicable) `source_url`. This is baked into the DB schema in §5, not bolted on later. |

---

## 2. Proposed architecture

```
                         ┌───────────────────────────┐
                         │        Orchestrator        │  (pipeline runner / job queue)
                         └─────────────┬─────────────┘
                                       │
   ┌───────────────────────────────────┼────────────────────────────────────┐
   │                                   │                                    │
┌──▼───────┐   ┌───────────┐   ┌───────▼────────┐   ┌──────────────┐  ┌─────▼──────┐
│  Crawler  │──▶│ Page Type │──▶│  Technical SEO │   │ SEO Data      │  │ Competitor │
│  Service  │   │ Classifier│   │   Screening    │   │ Provider Layer│──▶│ Discovery  │
└──────────┘   └───────────┘   └────────────────┘   │ (abstraction) │  └─────┬──────┘
                                                     └───────┬───────┘        │
                                                             │                │
                                       ┌─────────────────────▼────────────────▼───┐
                                       │   Keyword / Semantic Analyzer + Clustering │
                                       └─────────────────────┬──────────────────────┘
                                                             │
        ┌───────────────┬───────────────┬────────────────────┼───────────────┬───────────────┐
        │               │               │                    │               │               │
   ┌────▼────┐    ┌─────▼─────┐   ┌─────▼──────┐      ┌──────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
   │Competitor│    │  Content  │   │Page Structure│    │  Backlink  │   │  E-E-A-T  │   │ Quick Wins │
   │Benchmark │    │    Gap    │   │   Analyzer   │    │  Analyzer  │   │  Analyzer │   │  Analyzer  │
   └────┬────┘    └─────┬─────┘   └─────┬──────┘      └──────┬─────┘   └─────┬─────┘   └─────┬─────┘
        └───────────────┴───────────────┴────────────────────┴───────────────┴───────────────┘
                                                             │
                                                 ┌───────────▼───────────┐
                                                 │   Opportunity Engine   │
                                                 └───────────┬───────────┘
                                                 ┌───────────▼───────────┐
                                                 │ Scoring / Prioritization│
                                                 └───────────┬───────────┘
                                                 ┌───────────▼───────────┐
                                                 │  LLM Interpretation +  │
                                                 │   Grounding Validator  │
                                                 └───────────┬───────────┘
                                                 ┌───────────▼───────────┐
                                                 │ Report Generator +     │
                                                 │ Sales Talking Points   │
                                                 └────────────────────────┘
```

Data flow follows the brief's layering strictly:

```
RAW DATA  →  NORMALIZED DATA  →  CALCULATED METRICS  →  SEO GAPS  →  OPPORTUNITIES  →  LLM INTERPRETATION
```

Each arrow is a persisted table boundary (§5), not just an in-memory transformation — so any stage can be recomputed from the stage before it without re-purchasing API data or re-crawling.

### Architectural principles
- **Modules are independent services/packages**, each with a typed input and typed output, callable directly (function/class) in MVP and promotable to separate workers later without a rewrite.
- **Provider-independence**: nothing outside the `SEODataProvider` abstraction (§4) knows which vendor supplied the data.
- **Raw/normalized separation is mandatory** (§24): every external API response is stored verbatim before any normalization touches it.
- **Everything the LLM sees is pre-aggregated JSON**, never raw HTML or raw API payloads (§18).
- **Pipeline is resumable per stage** — a project can be re-run from "keyword analysis" onward without repeating the crawl, because each stage's output is a durable table, not a transient object.

---

## 3. Tech stack (proposed)

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.12 | Best ecosystem overlap for crawling, NLP, data processing, and every SEO-API SDK/example is Python or trivially callable via HTTP. |
| API/orchestration | FastAPI (thin API) + a plain pipeline runner (no heavyweight workflow engine for MVP) | Keeps MVP simple; Prefect/Dagster can be adopted in Phase 8 if batch/scheduling needs grow. |
| Task queue | Celery + Redis (introduced when async/parallel crawling of multiple competitors is needed) | Standard, easy to reason about; not required for a single-domain synchronous MVP run, but the module boundaries should already assume it. |
| Crawler | `httpx` (async) + `selectolax` for HTML parsing; `Playwright` for the JS-rendering fallback only | Fast static crawling by default, JS rendering only when triggered (see risk #4 above). |
| Database | PostgreSQL (with `JSONB` columns for raw payloads and flexible per-signal data) | Relational integrity for the pipeline's strict staging, JSONB where schema-per-row genuinely varies (raw API responses, LLM outputs). |
| Object storage | S3-compatible bucket (or local disk in dev) for raw HTML snapshots and large raw API payloads, referenced from Postgres by key | Keeps the DB lean; raw HTML for hundreds of pages doesn't belong in row storage. |
| LLM | Anthropic Claude (structured/tool-output calls for grounding) | Matches the environment this tool is being built in; strong structured-output and long-context support for the interpretation layer. |
| Embeddings (Phase 3+, semantic clustering) | Start with a local `sentence-transformers` model (no per-call cost, works offline) for MVP-adjacent clustering; revisit a hosted embeddings API only if quality demands it | Avoids adding a second paid vendor before it's proven necessary. |
| Report rendering | Jinja2 text templates → plain `.txt` output (no PDF/HTML rendering step) | Confirmed per §10: MVP output is plain text, so no PDF toolchain (WeasyPrint/wkhtmltopdf) is needed yet — that's a Phase 8 concern if/when a formatted deliverable is wanted. |
| Config | `pydantic-settings` + versioned YAML for scoring weights / exclude-lists / thresholds | Keeps the "configurable formula" and exclude-lists (per §17, §7) out of code. |
| Testing | `pytest`, fixture-recorded HTTP responses (`vcrpy` or similar) for provider calls | Pipeline correctness must be testable without spending real API budget on every CI run. |

---

## 4. External APIs needed

| Need | Recommended | Alternative(s) | Notes |
|---|---|---|---|
| Domain organic metrics, keywords, SERP, competitors, backlinks, referring domains — **one vendor covering most of §5/§6/§7/§13** | **DataForSEO** | Ahrefs API, Semrush API | DataForSEO is recommended as the MVP default: it's the only one of the three with metered, pay-as-you-go pricing across SERP + Keywords Data + Backlinks + On-Page/Content Analysis in one account, which matters a lot for an internal tool doing bursty, per-prospect analysis rather than continuous monitoring. Ahrefs/Semrush have materially higher fixed costs and more restrictive API tiers, but should stay pluggable via the same `SEODataProvider` interface (§7 of the brief) since agencies often already hold a Semrush/Ahrefs seat that could reduce marginal cost. **This choice needs sign-off — see §10.** |
| Core Web Vitals / page speed | Google PageSpeed Insights API | CrUX API | Free, no separate contract needed. |
| LLM interpretation, block classification, E-E-A-T signal extraction, grounding-adjacent structured output | Anthropic Claude API | — | Structured/tool-call output used everywhere an LLM touches page content, never free-form prose fed back into calculations. |
| Keyword/semantic clustering embeddings (post-MVP) | Local `sentence-transformers` model | Voyage AI embeddings API | Deferred; only add a paid embeddings vendor if local quality is insufficient. |
| Headless rendering (JS pages) | Self-hosted Playwright | Browserless.io (hosted) | Self-hosted by default; hosted only if infra ops overhead becomes a problem. |

### 4.1 API budget: fitting DataForSEO calls into $8/project

$8 is workable for the MVP call pattern **if the pipeline actively rations it**, not by default — DataForSEO bills per request/per row, and an MVP run touches client + up to 5 competitor domains. Rough shape of the spend (exact rates should be checked against DataForSEO's current price list before go-live — these are planning-level estimates, not a quote):

| Call | Domains touched | Rows/limit used | Rough cost |
|---|---|---|---|
| Domain metrics + 12mo history (Labs: Domain Rank Overview / Historical) | client + up to 5 competitors (≤6) | n/a (summary) | small, low cents per domain |
| Organic keywords (Labs: Ranked Keywords), capped `limit` | client + competitors (≤6) | capped at ~500–1000 rows/domain | the single biggest line item — scales directly with the row cap |
| Competitor discovery: SERP lookups for top N commercial keywords | n/a (query-based) | N = 20–30 queries (config, per risk §1.2) | second biggest line item — scales directly with N |
| Domain Competitors endpoint (if used instead of/alongside manual SERP discovery) | client | 1 call | small |
| Backlinks / referring domains | — | **not called in MVP** (Phase 5) | $0 |

**Guardrails this implies for MVP, not just a documented ceiling:**
- A **pre-flight cost estimator** runs before any paid call: given the planned row caps (`limit` per keyword pull) and query counts (N for competitor discovery), it sums an estimated cost and refuses to proceed past the configured budget (default $8/project) without an explicit override.
- Every `seo_metrics_raw` row stores its own `estimated_cost_usd`; a project's running total is checked against its budget before each new call, not just once at the start (so a partial run can't blow past budget by summing untracked calls).
- Defaults that keep spend low: keyword pull `limit` starts conservative (e.g. 300–500 rows/domain, raised only if the project needs deeper coverage), competitor discovery samples ≤5 competitors and ≤20 seed keywords, and Domain Competitors endpoint is preferred over full manual SERP intersection where it's cheaper for equivalent signal.
- If actual DataForSEO pricing (once verified against a live account) makes $8 too tight for the row caps needed for good-quality clusters, that's a decision to surface explicitly (raise the ceiling, or hold the row caps and accept thinner keyword coverage) — not something to quietly exceed.

This is why **T0.4** below (budget guardrail) is in Phase 0, before any paid call is wired up — the enforcement has to exist before the first real spend, not be bolted on after a project goes over.

---

## 5. Modules → services mapping

The 16 modules from §3 of the brief map onto the pipeline stages as follows (this is the module boundary the codebase should mirror):

| Module | Depends on | Produces | MVP? |
|---|---|---|---|
| 1. Site Crawler | domain input | `pages`, `page_links`, `page_images` | ✅ |
| 2. SEO Visibility Analyzer | SEODataProvider | `domain_metrics` (+ history) | ✅ |
| 3. Keyword/Semantic Analyzer | SEODataProvider, crawler output | `keywords`, `keyword_positions`, `clusters` | ✅ (simplified clustering) |
| 4. Competitor Discovery | SEODataProvider, keyword sample | `competitors` | ✅ |
| 5. Competitor Benchmark | domain_metrics (client+competitors) | `benchmark` | ✅ |
| 6. Content Gap Analyzer | clusters, competitor SERP presence | `content_gap` (part of `opportunities`) | ✅ |
| 7. Page Structure Analyzer | crawler + competitor page fetch + LLM | `page_structure_gap` | ⏸ Phase 4 |
| 8. Technical SEO Analyzer | crawler output | `technical_findings` | ✅ (screening subset only) |
| 9. Backlink Profile Analyzer | SEODataProvider | `backlink_profiles`, `referring_domains` | ⏸ Phase 5 |
| 10. E-E-A-T Analyzer | crawler + LLM | `eeat_signals` | ⏸ Phase 6 |
| 11. Quick Wins Analyzer | keyword_positions | `quick_wins` | ✅ |
| 12. SEO Opportunity Engine | all gap modules | `opportunities` | ✅ (4 of 9 gap types populated, rest placeholder) |
| 13. Priority/Scoring Engine | opportunities | scored `opportunities` | ✅ |
| 14. LLM Interpretation Layer | scored opportunities + metrics | interpretation JSON | ✅ |
| 15. Report Generator | interpretation + opportunities | report file | ✅ (reduced section set) |
| 16. Sales Talking Points Generator | interpretation | talking points object | ✅ |

Ecommerce Category Analysis (§11) is a variant of modules 1/3/6 gated by `website_type == ecommerce`; it is not a separate MVP task and is deferred alongside Page Structure (Phase 4) since it depends on the same competitor-page-fetch capability.

---

## 6. Database schema (proposed, MVP-scoped; full-system tables noted as future)

All tables carry `created_at`; tables holding externally-sourced or calculated data carry provenance columns explicitly (marked **prov.** below).

```
projects
  id, name, domain, target_country, target_language, business_type,
  website_type (services|ecommerce|saas|other), priority_services (jsonb),
  api_budget_usd (default 8.00), api_spend_usd (running total), created_at

domains                                   -- client + competitor domains, one row per hostname
  id, project_id, hostname, role (client|competitor),
  competitor_source (user_provided|discovered), relevance_score, added_at

crawls
  id, domain_id, started_at, finished_at, status, page_budget, pages_crawled

pages
  id, crawl_id, url, status_code, indexable (bool), robots_directives (jsonb),
  canonical, title, meta_description, h1, h2 (jsonb), h3 (jsonb),
  word_count, page_type, page_type_confidence, page_type_method (rule|llm),
  page_depth, structured_data (jsonb), breadcrumbs (jsonb), pagination (jsonb),
  hreflang (jsonb), content_hash, raw_html_ref (object storage key), rendered_with_js (bool)

page_links
  id, page_id, target_url, link_type (internal|external), anchor_text

page_images
  id, page_id, src, alt_text

seo_metrics_raw                            -- RAW, never mutated                [prov.]
  id, domain_id, provider, endpoint, request_params (jsonb), raw_response (jsonb),
  estimated_cost_usd, fetched_at

domain_metrics                             -- NORMALIZED, recomputable          [prov.]
  id, domain_id, date, organic_traffic, organic_keywords, top3, top10, top20, top100,
  traffic_value, branded_keywords, nonbranded_keywords, source_raw_id (fk seo_metrics_raw)

keywords
  id, project_id, text_normalized, locale, search_volume, cpc, competition,
  intent, intent_method (provider|heuristic|llm)

keyword_positions                                                              [prov.]
  id, keyword_id, domain_id, url, position, date, source_raw_id

clusters
  id, project_id, name, intent, total_search_volume, clustering_method, clustering_version

cluster_keywords
  cluster_id, keyword_id

cluster_url_map
  cluster_id, domain_id, url, best_position, opportunity_status (covered|weak|missing)

technical_findings                                                              [prov.]
  id, crawl_id, issue_type, severity (critical|notable|minor), affected_url_count,
  affected_urls_sample (jsonb), description, materiality_pct

opportunities
  id, project_id, type (traffic_gap|semantic_gap|commercial_page_gap|page_structure_gap|
       content_gap|backlink_gap|eeat_gap|technical_gap|quick_wins),
  title, description, evidence (jsonb, holds fk-like refs to source rows),
  impact, confidence, effort, business_relevance, score, scoring_version

reports
  id, project_id, generated_at, pipeline_version, sections (jsonb), file_ref, llm_run_id

sales_talking_points
  id, report_id, primary_angle, supporting_arguments (jsonb), quick_win_summary, what_to_sell (jsonb)

llm_runs                                                                        [prov.]
  id, project_id, stage (interpretation|talking_points|page_structure|eeat),
  model, input_payload (jsonb), output_payload (jsonb), validation_status
  (passed|regenerated|fallback), tokens_used, cost_estimate, created_at
```

**Deferred to their respective phases** (schema sketched now so Phase-4+ work doesn't require a redesign, not built in MVP): `page_blocks` (Page Structure), `backlink_profiles` / `referring_domains` (Backlinks), `eeat_signals` (E-E-A-T), `serp_results` (full SERP snapshots beyond what competitor discovery needs).

---

## 7. MVP definition

**Goal:** enter one domain + inputs from §2 of the brief, and get one working presale report + sales talking points, end-to-end, without a UI (CLI or script run) and without the modules that require competitor page scraping or backlink/E-E-A-T data.

**In scope:** Site Crawler (static only) → Page Type Classifier → Technical SEO Screening (materiality-filtered) → SEO Visibility Analyzer → Competitor Discovery (fallback) + Benchmark → Keyword collection + heuristic intent + simplified clustering → Missing Commercial Clusters → Quick Wins → Opportunity Engine (4 of 9 gap types) → Scoring → LLM Interpretation (with grounding validator) → Report Generator (reduced section set) → Sales Talking Points.

**Explicitly out of scope for MVP:** Page Structure Analyzer, Ecommerce Category Analysis, Backlink Profile Analyzer, E-E-A-T Analyzer, JS-rendering-by-default, any web UI/dashboard. The report's corresponding sections (5 Page Structure Gap, 6 Backlink Gap, 7 E-E-A-T/Trust Gap) render as an explicit "Not covered in this analysis (Phase 4/5/6)" placeholder rather than being silently omitted, so the report's structure doesn't need to change again later.

---

## 8. MVP development tasks & acceptance criteria

### Phase 0 — Foundations

**T0.1 — Project scaffolding**
Python package layout, dependency management, Docker Compose (Postgres + Redis), config loader, logging, CI skeleton.
*AC:* `docker compose up` boots Postgres; `python -m analyzer --help` runs; CI runs lint + an (initially trivial) test suite on push.

**T0.2 — Database schema & migrations**
Implement the MVP tables from §6 via Alembic migrations.
*AC:* `alembic upgrade head` creates all MVP tables; every provenance-bearing table has the columns marked `[prov.]` above; schema is documented (can be this file, kept in sync).

**T0.3 — SEODataProvider abstraction**
Define the interface (`get_domain_metrics`, `get_organic_keywords`, `get_top_pages`, `get_competitors`, `get_backlinks`, `get_referring_domains`, `get_keyword_metrics`, `get_serp`) and a DataForSEO implementation.
*AC:* interface defined as an ABC/Protocol; DataForSEO implementation covers at least the 6 methods MVP uses (backlinks/referring_domains may raise `NotImplementedError` for now but must exist in the interface); every provider call persists its raw response to `seo_metrics_raw` before any normalization; unit tests run against recorded fixture responses, not live API calls.

**T0.4 — API budget guardrail**
Pre-flight cost estimator + running-spend tracker enforcing the $8/project default ceiling (see §4.1) before any paid DataForSEO call executes.
*AC:* given a planned set of calls (row caps + query counts) that would exceed `api_budget_usd`, the pipeline refuses to start that stage and reports which planned call would breach the budget, instead of executing calls and finding out after the fact; every executed call updates `seo_metrics_raw.estimated_cost_usd` and the project's running `api_spend_usd`; the ceiling is config (not hardcoded), so it can be raised per-project with an explicit override flag.

### Phase 1 — Crawl & classify

**T1.1 — Site Crawler (static)**
Async, robots.txt-respecting, budget/depth-limited crawler extracting the §4 field set (minus semantic content blocks).
*AC:* a test run against a real small site populates `pages`/`page_links`/`page_images` with all listed fields; page budget and depth limit are config, not hardcoded; re-running against the same domain updates the existing crawl record rather than duplicating pages.

**T1.2 — Page Type Classifier**
Rule-based classifier (URL patterns, template signals) with an LLM fallback for ambiguous pages, assigning one of the §4 page types.
*AC:* ≥85% agreement with human-labeled review on a ≥50-page sample across at least 3 test sites; each page stores type + confidence + method; a helper reliably derives the "commercial pages" subset (service/category/product) used by every downstream module.

**T1.3 — Technical SEO Screening**
Aggregate crawl output into `technical_findings`, filtered by materiality (per the brief's "don't report cosmetic noise" rule).
*AC:* findings are grouped by issue type with affected-URL counts and a severity tag; an issue below the configured materiality threshold (e.g., affects <10% of commercial pages) does not appear in the report-facing output, only in a full/debug export.

### Phase 2 — Visibility & competitors

**T2.1 — SEO Visibility Analyzer**
Pull and normalize domain metrics + 6–12mo history; classify growth/stagnation/decline.
*AC:* `domain_metrics` populated with a `source_raw_id` back-reference; trend classification is a pure function over two comparable periods with a configurable threshold, unit-tested against fixture data.

**T2.2 — Competitor Discovery (fallback)**
When competitors aren't supplied, run SERP lookups over the client's top N commercial keywords, apply the exclude-list, rank by TOP-10 co-occurrence frequency.
*AC:* given zero user-supplied competitors, returns 3–5 ranked candidates with a relevance score; the exclude-list is a config file, not inline code; results are surfaced for user override before the pipeline continues (a project can be re-pointed at a manually-chosen competitor set without re-running discovery).

**T2.3 — Competitor Benchmark**
Compute client-vs-competitor-median metrics and gap ratios per §8.
*AC:* benchmark object includes client value, competitor median, and gap ratio for each metric in §8's list; missing data for one competitor doesn't fail the whole benchmark (median computed over available competitors, with a note on how many contributed).

### Phase 3 — Keywords, gaps, quick wins

**T3.1 — Keyword collection & normalization**
Pull organic keywords for client + competitors; normalize and dedupe into `keywords`/`keyword_positions`.
*AC:* keyword text is deduped by normalized-text + locale; positions carry date + source; re-import is idempotent.

**T3.2 — Intent classification**
Label each keyword commercial/transactional/informational/navigational using provider data where available, heuristic otherwise.
*AC:* ≥90% of total keyword search volume receives a non-null intent label; classification method is recorded per keyword.

**T3.3 — Simplified semantic clustering**
Group keywords into clusters (head-term/heuristic method for MVP) and populate `cluster_url_map` against client URLs already ranking/targeting them.
*AC:* cluster records match the §6 schema; clustering is deterministic for a given input + config version; a CSV/JSON export exists for manual QA of cluster quality before it feeds the content gap.

**T3.4 — Missing Commercial Clusters detector**
Flag commercial-intent clusters above a volume threshold as missing/weak/covered for the client.
*AC:* output sorted by volume, each entry showing competitor coverage count (e.g., "4/5 competitors rank"); feeds `opportunities` as `commercial_page_gap`/`semantic_gap`.

**T3.5 — Quick Wins Analyzer**
Identify positions 4–20, group by URL, compute combined volume and a priority score.
*AC:* output matches the §15 example shape (position-band counts, combined volume, priority score per URL); position window and score weights are config.

### Phase 3.5 — Opportunities, scoring, LLM, report

**T4.1 — Opportunity Engine (MVP subset)**
Populate `opportunities` from traffic_gap, technical_gap, semantic/commercial_page_gap, and quick_wins; leave the other 5 gap types as explicit "not analyzed" placeholders.
*AC:* every `opportunities` row references its evidence (source table + id); the 5 out-of-scope gap types exist as a documented empty/placeholder state the Report Generator already knows how to render.

**T4.2 — Scoring Engine**
Implement the configurable `Impact × Confidence × Business Relevance / Effort` formula with per-opportunity-type scoring rules in a versioned config file.
*AC:* changing the config changes ranking without a code change; each opportunity stores its 4 component values plus the resulting score, so the ranking is auditable, not just a final number.

**T4.3 — LLM Interpretation Layer + grounding validator**
Build the structured input object (§18 example) from calculated metrics/opportunities only; call Claude with a system prompt forbidding invented figures; validate every number in the output against the input object before accepting.
*AC:* a test asserts raw HTML/crawl content never appears in the LLM request payload; the grounding validator rejects a deliberately-corrupted test output containing a number absent from the input, triggering bounded regeneration or a templated fallback sentence.

**T4.4 — Report Generator**
Render the presale report (sections 1–4, 9–11 populated per §19; sections 5–7 shown as phase-deferred placeholders) as **plain text** (`.txt`) — no PDF/HTML rendering for MVP.
*AC:* a completed pipeline run produces a `.txt` report file with all required sections present, in the order given in §19, readable as-is (fixed-width friendly, no markup); every factual claim in the text is traceable to a source record id (kept in the run's metadata/log even though it isn't printed inline in the plain-text body); running against a real test project produces a file a sales manager could read and use without any further formatting step.

**T4.5 — Sales Talking Points Generator**
Produce PRIMARY SALES ANGLE / SUPPORTING ARGUMENTS / QUICK WIN / WHAT TO SELL as a structured object separate from the client-facing report.
*AC:* stored linked to the report id; every figure quoted passes the same grounding validator as T4.3.

**T4.6 — CLI pipeline runner**
`analyzer run --domain ... --country ... --language ... --business-type ... --site-type ... [--competitors ...]` executes the full MVP pipeline and writes report + talking points to disk.
*AC:* one command runs a real domain through the full pipeline end to end without manual steps between stages; a provider timeout or partial failure at any stage is logged and reflected as a caveat in the report rather than crashing the whole run; a re-run within the configured freshness window reuses cached raw data instead of re-hitting paid APIs.

---

## 9. Post-MVP phases (as scoped in the brief, unchanged)

Phase 4 (SERP collection + competitor page parsing + Page Structure Gap) → Phase 5 (Backlinks + Backlink Gap) → Phase 6 (E-E-A-T) → Phase 7 remainder (full 9-type Opportunity Engine, richer scoring) → Phase 8 (UI/dashboard). Each phase slots into the architecture in §2 without restructuring it — this is the point of designing the schema and the Opportunity Engine's 9-type shape up front (§6, §5) even though MVP only populates 4 of them.

---

## 10. Decisions needed before development starts

1. ✅ **Primary SEO data provider** — **resolved: DataForSEO.**
2. ✅ **Per-project API budget ceiling** — **resolved: $8/project**, enforced by T0.4's guardrail (see §4.1). Drives the row caps and query counts used by Competitor Discovery and keyword collection.
3. **Crawl scope/budget default** — max pages and max depth per client crawl (affects cost, runtime, and how much "orphan pages"/"true depth" claims can be trusted, per risk #6 in §1). Still open — proposed default to confirm: 300 pages / depth 5 for a `services` or `saas` site, higher for `ecommerce` given category/product volume; adjustable per project.
4. **JS rendering policy** — off by default with a heuristic trigger (as proposed in §1, risk #4), or always-on for a specific site-type (e.g. SaaS marketing sites tend to be JS-heavy)? Still open.
5. **Legal/compliance sign-off on crawling prospect + competitor sites** — **in progress.** A fill-in template is provided at [`LEGAL_SIGNOFF.md`](./LEGAL_SIGNOFF.md) in this same folder — see §12 below for what to fill in and how it gates Phase 1. Crawler work (T1.1) should not run against real prospect/competitor domains until that document is completed and committed.
6. **LLM/embeddings vendor** — Claude for interpretation/structured extraction (proposed default given the environment), and local `sentence-transformers` vs. a paid embeddings API for clustering, deferred to Phase 3+. Still open (low urgency — doesn't block MVP Phase 0–3).
7. ✅ **Output format** — **resolved: plain text.** MVP report and talking points are `.txt` output; no PDF/HTML rendering, no slide-deck generation (the existing `SEO_Strategy_*.pptx` decks in this repo are a separate, manually-built deliverable and out of scope for the analyzer's MVP output).
8. **Scoring weights v1** — the Impact/Confidence/Effort/Business-Relevance formula and per-opportunity-type rules are a first-guess calibration (§1, risk #11); confirm who owns validating/adjusting these against real sales outcomes. Still open.
9. **Data retention/privacy** — how long raw crawl/API data for a prospect (not yet a client) is retained, and whether prospects need to be informed their public site was analyzed. Still open — folded into the legal sign-off template (§12).
10. **Hosting** — where this runs (internal server, cloud VM, containers) — affects whether Redis/Celery/Playwright infra is provisioned from day one or deferred until parallel/batch processing is actually needed. Still open, but doesn't block Phase 0–3 (a local/single-machine run is enough for MVP).

Remaining open items (#3, #4, #6, #8, #10) are lower-stakes than #1/#2/#5/#7 and don't have to block starting Phase 0 — they can be defaulted per the proposed values above and revisited before Phase 1's crawler goes live against a real prospect domain.

---

## 11. API keys / credentials needed

- **DataForSEO** — API login + password (or equivalent token), pending decision in §10.1.
- **Anthropic (Claude)** — API key, for interpretation, page-block classification, and E-E-A-T signal extraction (Phase 6+).
- **Google PageSpeed Insights** — API key (free tier available) for Core Web Vitals.
- **Object storage** (S3-compatible: AWS S3 / DigitalOcean Spaces / MinIO self-hosted) — access key + secret, for raw HTML snapshots and large raw payloads.
- **PostgreSQL** — connection credentials for whichever environment hosts it (local Docker for dev; managed instance for anything persistent).
- **Optional, deferred:** Ahrefs or Semrush API key (only if adopted as an alternate/secondary provider), a hosted embeddings API key (only if local embeddings prove insufficient), Browserless/hosted-Playwright credentials (only if self-hosted rendering becomes an ops burden).

---

## 12. Legal / compliance sign-off — what to add and where

This gates one specific thing: **T1.1 (Site Crawler) must not be pointed at a real prospect's or a real competitor's live domain** until this is filled in and committed. Everything else in Phase 0–3 (scaffolding, schema, provider abstraction, DataForSEO calls, keyword/visibility analysis) doesn't touch a third party's site directly and isn't blocked by this.

**What to add:** fill in [`LEGAL_SIGNOFF.md`](./LEGAL_SIGNOFF.md) in this folder — it's a template with the specific fields that matter for this tool (who approved it, the crawl policy the tool will actually follow, data retention, and what happens if a site owner objects). It doesn't need to be a formal legal document — it needs to be a clear, dated record that someone with authority to decide this for the agency looked at the crawl policy and approved it, so this decision isn't made silently by whoever happens to write the crawler code.

**How it gates development:** once `LEGAL_SIGNOFF.md` has the "Approved" fields filled in, T1.1 can run against real domains. Until then, T1.1 can still be built and tested against domains you own or explicitly control (e.g. a test site, or this repo's own site) — the sign-off blocks *production use against prospects*, not the engineering work itself.

---

*This plan intentionally stops here. No pipeline code has been written. Next step is resolving the remaining open items in §10 (crawl budget, JS rendering policy, scoring weights, hosting — all lower-stakes and default-able) and completing `LEGAL_SIGNOFF.md`, after which Phase 0–3 tasks in §8 can start.*
