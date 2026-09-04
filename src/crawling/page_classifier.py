"""Classifies a crawled page's likely purpose, from its URL path and (as a
fallback) its title/heading text. Used by:
  * community/event discovery (Stage 5/6) to find members/board/speakers
    pages worth extracting people from
  * the company website crawler (Stage 13) to decide which pages to look at
    for founder/leadership info
"""

from __future__ import annotations

import re
from enum import Enum


class PageCategory(str, Enum):
    HOME = "home"
    ABOUT = "about"
    TEAM = "team"
    LEADERSHIP = "leadership"
    MANAGEMENT = "management"
    CONTACT = "contact"
    COMPANY = "company"
    BLOG = "blog"
    AUTHORS = "authors"
    PRESS = "press"
    MEDIA = "media"
    CAREERS = "careers"

    MEMBERS = "members"
    DIRECTORY = "directory"
    BOARD = "board"
    SPEAKERS = "speakers"
    PARTICIPANTS = "participants"
    SPONSORS = "sponsors"
    PARTNERS = "partners"
    COMPANIES = "companies"
    FOUNDERS = "founders"

    OTHER = "other"


# Each path segment is split into whole alnum tokens and matched against
# these keyword sets *exactly* -- not as a substring search. This matters
# in practice: a naive substring match on "/company" also matches inside
# "/companies" (picking the wrong, less specific category), "board" matches
# inside "dashboard", "team" could match inside a longer slug, etc. Order
# is still meaningful when a segment's tokens satisfy more than one rule
# (e.g. "member-directory" -> tokens {"member","directory"} matches both
# MEMBERS and DIRECTORY; MEMBERS wins because it's listed first) but no
# rule can ever fire just because its keyword is a *substring* of a token
# it doesn't equal.
_TOKEN_RULES: list[tuple[frozenset[str], PageCategory]] = [
    (frozenset({"about"}), PageCategory.ABOUT),
    (frozenset({"team"}), PageCategory.TEAM),
    (frozenset({"leadership"}), PageCategory.LEADERSHIP),
    (frozenset({"management"}), PageCategory.MANAGEMENT),
    (frozenset({"contact", "contacts"}), PageCategory.CONTACT),
    (frozenset({"company"}), PageCategory.COMPANY),
    (frozenset({"blog"}), PageCategory.BLOG),
    (frozenset({"author", "authors"}), PageCategory.AUTHORS),
    (frozenset({"press"}), PageCategory.PRESS),
    (frozenset({"media"}), PageCategory.MEDIA),
    (frozenset({"career", "careers"}), PageCategory.CAREERS),
    (frozenset({"member", "members"}), PageCategory.MEMBERS),
    (frozenset({"directory"}), PageCategory.DIRECTORY),
    (frozenset({"board"}), PageCategory.BOARD),
    (frozenset({"speaker", "speakers"}), PageCategory.SPEAKERS),
    (frozenset({"participant", "participants"}), PageCategory.PARTICIPANTS),
    (frozenset({"sponsor", "sponsors"}), PageCategory.SPONSORS),
    (frozenset({"partner", "partners"}), PageCategory.PARTNERS),
    (frozenset({"companies"}), PageCategory.COMPANIES),
    (frozenset({"founder", "founders"}), PageCategory.FOUNDERS),
]

_TOKEN_SPLIT_RE = re.compile(r"[^a-z0-9]+")


def _segment_tokens(path: str) -> list[str]:
    """All lowercase alnum tokens across every path segment, e.g.
    "/about-us/team/" -> ["about", "us", "team"]; "/list-of-members/" ->
    ["list", "of", "members"].
    """
    return [t for t in _TOKEN_SPLIT_RE.split((path or "").lower()) if t]


def classify_path(path: str) -> PageCategory:
    tokens = set(_segment_tokens(path))
    if not tokens:
        return PageCategory.HOME
    for keywords, category in _TOKEN_RULES:
        if tokens & keywords:
            return category
    return PageCategory.OTHER


# Pages worth extracting person records from (community/event discovery).
PERSON_BEARING_CATEGORIES = {
    PageCategory.MEMBERS,
    PageCategory.DIRECTORY,
    PageCategory.BOARD,
    PageCategory.LEADERSHIP,
    PageCategory.SPEAKERS,
    PageCategory.PARTICIPANTS,
    PageCategory.SPONSORS,
    PageCategory.PARTNERS,
    PageCategory.COMPANIES,
    PageCategory.FOUNDERS,
    PageCategory.TEAM,
    PageCategory.MANAGEMENT,
    PageCategory.ABOUT,
}


def is_person_bearing(category: PageCategory) -> bool:
    return category in PERSON_BEARING_CATEGORIES
