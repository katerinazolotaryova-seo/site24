"""Normalization helpers for companies and people.

Keeps normalization logic in one place so discovery, dedup, matching and
export all agree on what a "domain" or "clean name" looks like.
"""

from __future__ import annotations

import re
from typing import Optional

import tldextract

from src.models import Company, Person

# suffix_list_urls=() disables tldextract's live public-suffix-list fetch
# on first use -- we run in network-restricted/offline environments and
# must never let a domain-parsing call block on (or fail from) a network
# request. Falls back to the snapshot bundled with the package.
_TLD_EXTRACTOR = tldextract.TLDExtract(suffix_list_urls=())

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]")
_LEGAL_SUFFIXES = {
    "inc", "inc.", "llc", "llc.", "l.l.c.", "ltd", "ltd.", "corp", "corp.",
    "corporation", "co", "co.", "company", "plc", "llp", "pllc", "pc",
    "group", "holdings", "the",
}

_PHONE_STRIP_RE = re.compile(r"[^\d+]")


def normalize_whitespace(text: str) -> str:
    return _WS_RE.sub(" ", text or "").strip()


def normalize_domain(url_or_domain: Optional[str]) -> Optional[str]:
    """Returns the registrable domain (e.g. "example.com") for a URL or bare
    domain, stripping scheme/www/path/query. Returns None if unparseable.
    """
    if not url_or_domain:
        return None
    value = url_or_domain.strip()
    if not value:
        return None
    ext = _TLD_EXTRACTOR(value)
    if not ext.domain or not ext.suffix:
        return None
    return f"{ext.domain}.{ext.suffix}".lower()


def normalize_company_name(name: Optional[str]) -> str:
    """Lowercased, punctuation-stripped, legal-suffix-stripped company name
    used as a dedup key (Stage 15). Not for display -- keep the original
    `company_name` for that.
    """
    if not name:
        return ""
    cleaned = _PUNCT_RE.sub(" ", name.lower())
    cleaned = normalize_whitespace(cleaned)
    tokens = [t for t in cleaned.split(" ") if t and t not in _LEGAL_SUFFIXES]
    return " ".join(tokens)


def normalize_person_name(name: Optional[str]) -> str:
    if not name:
        return ""
    cleaned = normalize_whitespace(name)
    # Strip common credential/suffix noise ("John Smith, MBA")
    cleaned = re.sub(r",.*$", "", cleaned)
    return cleaned.strip()


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    digits = _PHONE_STRIP_RE.sub("", phone)
    if len(digits.lstrip("+")) < 7:
        return None
    return digits


def normalize_title(title: Optional[str]) -> str:
    if not title:
        return ""
    cleaned = normalize_whitespace(title.lower())
    cleaned = _PUNCT_RE.sub(" ", cleaned).replace("  ", " ")
    return normalize_whitespace(cleaned)


def clean_state(state: Optional[str]) -> Optional[str]:
    if not state:
        return None
    return normalize_whitespace(state).title()


def clean_city(city: Optional[str]) -> Optional[str]:
    if not city:
        return None
    return normalize_whitespace(city).title()


def normalize_company(company: Company) -> Company:
    company.company_name = normalize_whitespace(company.company_name)
    if company.website and not company.domain:
        company.domain = normalize_domain(company.website)
    elif company.domain:
        company.domain = normalize_domain(company.domain)
    company.city = clean_city(company.city)
    company.state = clean_state(company.state)
    return company


def normalize_person(person: Person) -> Person:
    person.full_name = normalize_person_name(person.full_name)
    if person.company_domain:
        person.company_domain = normalize_domain(person.company_domain)
    person.city = clean_city(person.city)
    person.state = clean_state(person.state)
    if person.original_job_title:
        person.original_job_title = normalize_whitespace(person.original_job_title)
    return person
