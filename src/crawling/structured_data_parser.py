"""Extracts structured facts from an already-fetched HTML page:
  * JSON-LD blocks, especially schema.org Person / Organization
  * mailto: / tel: links
  * social profile links (LinkedIn, Facebook, Instagram, Telegram)
  * plain-text email/phone patterns as a fallback

Pure parsing -- no network calls -- so it's cheap to unit test and reuse
between the community-site crawler and the company-site crawler.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from selectolax.parser import HTMLParser

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")

SOCIAL_DOMAIN_PATTERNS = {
    "linkedin": re.compile(r"linkedin\.com/(?:in|company)/[\w\-%.]+", re.IGNORECASE),
    "facebook": re.compile(r"facebook\.com/[\w\-.]+", re.IGNORECASE),
    "instagram": re.compile(r"instagram\.com/[\w\-.]+", re.IGNORECASE),
    "telegram": re.compile(r"(?:t\.me|telegram\.me)/[\w\-]+", re.IGNORECASE),
}


@dataclass
class ExtractedPageData:
    emails: set[str] = field(default_factory=set)
    phones: set[str] = field(default_factory=set)
    social_links: dict[str, set[str]] = field(default_factory=lambda: {k: set() for k in SOCIAL_DOMAIN_PATTERNS})
    json_ld_people: list[dict] = field(default_factory=list)
    json_ld_orgs: list[dict] = field(default_factory=list)
    title: str | None = None
    headings: list[str] = field(default_factory=list)
    text_snippet: str = ""


def parse_page(html: str, base_url: str = "") -> ExtractedPageData:
    data = ExtractedPageData()
    if not html:
        return data

    tree = HTMLParser(html)

    title_node = tree.css_first("title")
    if title_node:
        data.title = title_node.text(strip=True)

    for tag in ("h1", "h2"):
        for node in tree.css(tag):
            text = node.text(strip=True)
            if text:
                data.headings.append(text)

    # mailto / tel links
    for a in tree.css("a[href^='mailto:']"):
        href = a.attributes.get("href", "")
        email = href.replace("mailto:", "").split("?")[0].strip()
        if email:
            data.emails.add(email.lower())

    for a in tree.css("a[href^='tel:']"):
        href = a.attributes.get("href", "")
        phone = href.replace("tel:", "").strip()
        if phone:
            data.phones.add(phone)

    # social links + generic hrefs
    for a in tree.css("a[href]"):
        href = a.attributes.get("href", "") or ""
        for platform, pattern in SOCIAL_DOMAIN_PATTERNS.items():
            m = pattern.search(href)
            if m:
                data.social_links[platform].add("https://" + m.group(0))

    body_text = tree.body.text(separator=" ", strip=True) if tree.body else tree.text(separator=" ", strip=True)
    data.text_snippet = body_text[:4000]

    for m in EMAIL_RE.finditer(body_text):
        data.emails.add(m.group(0).lower())
    for m in PHONE_RE.finditer(body_text):
        data.phones.add(m.group(0))

    # JSON-LD
    for script in tree.css("script[type='application/ld+json']"):
        raw = script.text(strip=True)
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for obj in _flatten_jsonld(payload):
            obj_type = obj.get("@type")
            types = obj_type if isinstance(obj_type, list) else [obj_type]
            if any(t and str(t).lower() == "person" for t in types):
                data.json_ld_people.append(obj)
            elif any(t and str(t).lower() in {"organization", "corporation", "localbusiness"} for t in types):
                data.json_ld_orgs.append(obj)

    return data


def _flatten_jsonld(payload) -> list[dict]:
    out: list[dict] = []
    if isinstance(payload, list):
        for item in payload:
            out.extend(_flatten_jsonld(item))
    elif isinstance(payload, dict):
        out.append(payload)
        for key in ("@graph", "employee", "founder", "member"):
            nested = payload.get(key)
            if isinstance(nested, (list, dict)):
                out.extend(_flatten_jsonld(nested))
    return out


def person_from_jsonld(obj: dict) -> dict:
    """Maps a schema.org Person JSON-LD object to our loose extraction dict."""
    name = obj.get("name")
    job_title = obj.get("jobTitle")
    same_as = obj.get("sameAs") or []
    if isinstance(same_as, str):
        same_as = [same_as]
    email = obj.get("email")
    if isinstance(email, str):
        email = email.replace("mailto:", "")
    return {
        "full_name": name,
        "job_title": job_title,
        "email": email,
        "profile_links": same_as,
    }
