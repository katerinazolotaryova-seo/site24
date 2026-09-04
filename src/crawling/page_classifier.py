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


_PATH_PATTERNS: list[tuple[re.Pattern, PageCategory]] = [
    (re.compile(r"^/?$"), PageCategory.HOME),
    (re.compile(r"about[-_]?us|/about"), PageCategory.ABOUT),
    (re.compile(r"/team"), PageCategory.TEAM),
    (re.compile(r"leadership"), PageCategory.LEADERSHIP),
    (re.compile(r"management"), PageCategory.MANAGEMENT),
    (re.compile(r"contact"), PageCategory.CONTACT),
    (re.compile(r"/company"), PageCategory.COMPANY),
    (re.compile(r"/blog"), PageCategory.BLOG),
    (re.compile(r"authors?"), PageCategory.AUTHORS),
    (re.compile(r"press"), PageCategory.PRESS),
    (re.compile(r"media"), PageCategory.MEDIA),
    (re.compile(r"career"), PageCategory.CAREERS),
    (re.compile(r"members?"), PageCategory.MEMBERS),
    (re.compile(r"directory"), PageCategory.DIRECTORY),
    (re.compile(r"board"), PageCategory.BOARD),
    (re.compile(r"speakers?"), PageCategory.SPEAKERS),
    (re.compile(r"participants?"), PageCategory.PARTICIPANTS),
    (re.compile(r"sponsors?"), PageCategory.SPONSORS),
    (re.compile(r"partners?"), PageCategory.PARTNERS),
    (re.compile(r"companies"), PageCategory.COMPANIES),
    (re.compile(r"founders?"), PageCategory.FOUNDERS),
]

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


def classify_path(path: str) -> PageCategory:
    lowered = (path or "").lower()
    for pattern, category in _PATH_PATTERNS:
        if pattern.search(lowered):
            return category
    return PageCategory.OTHER


def is_person_bearing(category: PageCategory) -> bool:
    return category in PERSON_BEARING_CATEGORIES
