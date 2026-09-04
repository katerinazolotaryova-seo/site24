from src.models import NormalizedRole
from src.processing.role_classifier import RoleClassifier


def test_classifies_common_titles():
    clf = RoleClassifier()
    cases = {
        "Founder & CEO": NormalizedRole.FOUNDER,
        "Co-Founder": NormalizedRole.CO_FOUNDER,
        "Chief Marketing Officer": NormalizedRole.CMO,
        "VP of Marketing": NormalizedRole.VP_MARKETING,
        "Head of Growth": NormalizedRole.HEAD_OF_GROWTH,
        "Director of Marketing": NormalizedRole.MARKETING_DIRECTOR,
        "Head of SEO": NormalizedRole.HEAD_OF_SEO,
        "Random Software Engineer": NormalizedRole.OTHER,
    }
    for title, expected in cases.items():
        assert clf.classify(title) == expected, f"{title} -> expected {expected}, got {clf.classify(title)}"


def test_empty_title_is_other():
    clf = RoleClassifier()
    assert clf.classify(None) == NormalizedRole.OTHER
    assert clf.classify("") == NormalizedRole.OTHER
