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

import html
import re

from src.crawling.structured_data_parser import ExtractedPageData, person_from_jsonld

# "Jane Smith, CEO" / "Jane Smith - Founder" / "Jane Smith — Head of Marketing"
_NAME_TITLE_RE = re.compile(
    r"^(?P<name>[A-Z][a-zA-Z.'\-]+(?:\s+[A-Z][a-zA-Z.'\-]+){1,3})\s*[,\-–—]\s*(?P<title>[A-Za-z][A-Za-z &/,]{2,60})$"
)

# JSON-LD Person blocks on real-world sites are frequently boilerplate
# author/publisher metadata injected by CMS/SEO plugins (WordPress + Yoast
# in particular love to stamp every page with a schema.org Person whose
# "name" is really the technical author *username* or even the bare
# domain) rather than an actual staff/leadership listing. We only accept a
# candidate name that plausibly looks like "First Last": at least two
# words, no dots/@ (rules out domains and emails), no bare URLs.
_DOMAIN_OR_EMAIL_RE = re.compile(r"[./@]|https?://")


def _looks_like_a_real_person_name(name: str) -> bool:
    if not name or len(name) > 80:
        return False
    if _DOMAIN_OR_EMAIL_RE.search(name):
        return False
    words = name.split()
    return len(words) >= 2 and all(w[:1].isalpha() for w in words)


# Member-listing pages ("Aero Precision, LLC", "Culmen International, LLC")
# format company names the same way a person listing formats "Name, Title"
# -- name, comma, short capitalized fragment. A legal-entity suffix as the
# "title" is the tell that this is a company name, not a person.
_LEGAL_SUFFIX_TITLES = {
    "llc", "inc", "inc.", "corp", "corp.", "corporation", "ltd", "ltd.",
    "llp", "pllc", "pc", "co", "co.", "company", "group", "plc", "l.l.c.",
}


def _looks_like_a_real_job_title(title: str | None) -> bool:
    if not title:
        return True  # absent title is fine -- just means "unknown role"
    return title.strip().lower().rstrip(".") not in _LEGAL_SUFFIX_TITLES


def _dedupe_repeated_text(text: str) -> str:
    """Some real-world pages ship a JSON-LD org/site "name" field that
    accidentally concatenates the same name twice -- once raw, once
    HTML-entity-escaped (a common WordPress/SEO-plugin bug). Collapse
    "X X" back down to "X" when both halves are the same string once
    entities are unescaped.
    """
    unescaped = html.unescape(text).strip()
    words = unescaped.split()
    n = len(words)
    if n >= 4 and n % 2 == 0:
        half = n // 2
        first, second = " ".join(words[:half]), " ".join(words[half:])
        if first.lower() == second.lower():
            return first
    return unescaped


def extract_person_candidates(data: ExtractedPageData, source_url: str) -> list[dict]:
    candidates: list[dict] = []
    seen_names: set[str] = set()

    for obj in data.json_ld_people:
        parsed = person_from_jsonld(obj)
        name = (parsed.get("full_name") or "").strip()
        if not name or name.lower() in seen_names:
            continue
        if not _looks_like_a_real_person_name(name):
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
        title = m.group("title").strip()
        if name.lower() in seen_names or not _looks_like_a_real_person_name(name) or not _looks_like_a_real_job_title(title):
            continue
        seen_names.add(name.lower())
        candidates.append(
            {
                "full_name": name,
                "job_title": title,
                "email": None,
                "profile_links": [],
                "source_url": source_url,
                "extraction_method": "heading_pattern",
            }
        )

    return candidates


def _json_ld_org_matches_page_subject(name: str, data: ExtractedPageData) -> bool:
    """A JSON-LD Organization block is frequently CMS/SEO-plugin boilerplate
    describing the *site itself* (WordPress/Yoast in particular stamps the
    same "publisher" Organization on literally every page of a domain),
    not the specific company a detail page is actually about. Only trust
    it if its name plausibly appears in this page's own title/headings --
    real evidence the block is *about this page*, not generic site
    identity.
    """
    haystack = " ".join([data.title or "", *data.headings]).lower()
    return bool(haystack) and name.lower() in haystack


def extract_company_candidate(data: ExtractedPageData, source_url: str, allow_title_fallback: bool = True) -> dict | None:
    """Guesses the single company a page is *about*. Appropriate for a
    single-subject page (a company's own /about page, a bio page for one
    founder). NOT appropriate for a listing page (members/sponsors/
    directory) that names many companies -- pass `allow_title_fallback=
    False` there, since the page <title> ("Business Members Directory")
    describes the listing, not any one company on it; use
    `extract_company_candidates_from_headings` for those instead.
    """
    for obj in data.json_ld_orgs:
        name = (obj.get("name") or "").strip()
        if name and _json_ld_org_matches_page_subject(name, data):
            return {
                "company_name": _dedupe_repeated_text(name),
                "website": obj.get("url") or source_url,
                "source_url": source_url,
                "extraction_method": "json_ld",
            }
    if data.title and allow_title_fallback:
        # Weak fallback: page <title> as a company-name guess. Downstream
        # CompanyMatcher/dedup will reconcile this against stronger hits.
        cleaned = re.split(r"[|–—-]", data.title)[0].strip()
        if cleaned:
            return {
                "company_name": _dedupe_repeated_text(cleaned),
                "website": source_url,
                "source_url": source_url,
                "extraction_method": "page_title",
            }
    return None


def extract_company_candidates_from_headings(data: ExtractedPageData, source_url: str) -> list[dict]:
    """Member/sponsor/partner listing pages often render each company as a
    heading shaped exactly like a person listing -- "Name, Title" --
    except the "title" slot is a legal-entity suffix ("Aero Precision,
    LLC") rather than a job title. Reuses the same name/title heading
    pattern and keeps only the matches `extract_person_candidates` itself
    rejects for that reason, so the same heading is never double-counted
    as both a person and a company.
    """
    out: list[dict] = []
    seen: set[str] = set()
    for heading in data.headings:
        m = _NAME_TITLE_RE.match(heading.strip())
        if not m:
            continue
        suffix = m.group("title").strip()
        if _looks_like_a_real_job_title(suffix):
            continue  # a real job title -- this is a person heading, not a company one
        name = f"{m.group('name').strip()}, {suffix}"
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "company_name": name,
                "website": None,
                "source_url": source_url,
                "extraction_method": "heading_pattern",
            }
        )
    return out
