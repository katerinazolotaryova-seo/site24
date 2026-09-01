# Legal / Compliance Sign-off — Crawling Prospect & Competitor Sites

Status: **NOT YET APPROVED — template only.**

This document exists to record a deliberate decision, not to create legal risk by itself. Until the "Approved" section at the bottom is filled in and this file is committed, the Site Crawler (T1.1) must only be run against domains you own or explicitly control (test sites, this agency's own site) — never against a real prospect's or competitor's live domain.

Fill in every section below, then the "Approved" block at the end.

---

## 1. What the crawler will actually do

This is the policy the crawler is built to follow (per `ARCHITECTURE_AND_MVP_PLAN.md` §1, risk #9). Confirm or edit each line so it matches what you're actually approving:

- [ ] Crawls only the **prospect's own public site** during presale analysis, plus a small, targeted set of **specific competitor page URLs** (the ones identified via SERP as ranking for the prospect's priority keywords) — never a full crawl of a competitor's site.
- [ ] Respects `robots.txt` and any `noindex`/`nofollow` directives it encounters; does not attempt to bypass logins, paywalls, or any access control.
- [ ] Identifies itself with a clear, non-deceptive User-Agent string (e.g. naming the agency and a contact URL/email), so a site owner who notices the traffic can find out who it is.
- [ ] Applies a reasonable crawl rate/delay so it does not measurably burden the target site (this is manual-research-equivalent volume, not bulk scraping).
- [ ] Stores only what's needed for the analysis (page content, structure, metadata) — not an indiscriminate mirror of the site.
- [ ] Does not republish or resell scraped competitor content; it's used only internally, to build the presale report and talking points.

## 2. Data retention

- Raw crawl data (HTML snapshots, extracted page data) for a **prospect's** site is retained for: ______________ (e.g. "90 days after the presale report is delivered, then deleted unless the prospect becomes a client").
- Raw crawl data for **competitor** pages fetched during analysis is retained for: ______________
- Who is responsible for actually deleting data once the retention window passes: ______________

## 3. Prospect notification

- [ ] Prospects are **not** proactively notified that their public site was analyzed before a sales conversation (standard presale-research practice), **or**
- [ ] Prospects **are** notified (specify when/how): ______________

## 4. What happens if a site owner objects

- If a prospect or competitor asks for their data to be removed or objects to being crawled, the response is: ______________ (e.g. "delete on request, no further crawling of that domain").
- Point of contact for such requests: ______________

## 5. Scope limits

- [ ] This sign-off covers the crawler behavior described in §1 only. Any future change that meaningfully increases crawl volume, targets a broader set of competitor pages, or adds new data collection (e.g. following external links beyond the priority-page set) should be re-reviewed against this document rather than assumed to already be covered.

---

## Approved

- **Approved by:** ______________
- **Role/authority:** ______________
- **Date:** ______________
- **Notes/conditions (if any):** ______________

Once this section is filled in, T1.1 (Site Crawler) is cleared to run against real prospect and competitor domains under the policy described in §1 above.
