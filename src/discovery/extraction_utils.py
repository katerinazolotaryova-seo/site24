"""Shared heuristics for pulling person/company candidates out of an
already-fetched, already-parsed page (ExtractedPageData). Used by
directory_discovery, event_discovery, founder_discovery and
marketer_discovery so they all agree on what "a name + a title" looks like
on a page.

Every candidate returned here is a *discovery candidate*, not a verified
fact -- normalization, role classification, matching and Ukraine-connection
verification all happen downstream.
"""

from __future__ import annotations

import re

from src.crawling.structured_data_parser import ExtractedPageData, person_from_jsonld

# "Jane Smith, CEO" / "Jane Smith - Founder" / "Jane Smith — Head of Marketing"
_NAME_TITLE_RE = re.compile(
    r"^(?P<name>[A-Z][a-zA-Z.'\-]+(?:\s+[A-Z][a-zA-Z.'\-]+){1,3})\s*[,\-–—]\s*(?P<title>[A-Za-z][A-Za-z &/,]{2,60})$"
)


def extract_person_candidates(data: ExtractedPageData, source_url: str) -> list[dict]:
    candidates: list[dict] = []
    seen_names: set[str] = set()

    for obj in data.json_ld_people:
        parsed = person_from_jsonld(obj)
        name = (parsed.get("full_name") or "").strip()
        if not name or name.lower() in seen_names:
            continue
        seen_names.add(name.lower())
        candidates.append(
            {
                "full_name": name,
                "job_title": parsed.get("job_title"),
                "email": parsed.get("email"),
                "profile_links": parsed.get("profile_links") or [],
                "source_url": source_url,
                "extraction_method": "json_ld",
            }
        )

    for heading in data.headings:
        m = _NAME_TITLE_RE.match(heading.strip())
        if not m:
            continue
        name = m.group("name").strip()
        if name.lower() in seen_names:
            continue
        seen_names.add(name.lower())
        candidates.append(
            {
                "full_name": name,
                "job_title": m.group("title").strip(),
                "email": None,
                "profile_links": [],
                "source_url": source_url,
                "extraction_method": "heading_pattern",
            }
        )

    return candidates


def extract_company_candidate(data: ExtractedPageData, source_url: str) -> dict | None:
    for obj in data.json_ld_orgs:
        name = (obj.get("name") or "").strip()
        if name:
            return {
                "company_name": name,
                "website": obj.get("url") or source_url,
                "source_url": source_url,
                "extraction_method": "json_ld",
            }
    if data.title:
        # Weak fallback: page <title> as a company-name guess. Downstream
        # CompanyMatcher/dedup will reconcile this against stronger hits.
        cleaned = re.split(r"[|–—-]", data.title)[0].strip()
        if cleaned:
            return {
                "company_name": cleaned,
                "website": source_url,
                "source_url": source_url,
                "extraction_method": "page_title",
            }
    return None
