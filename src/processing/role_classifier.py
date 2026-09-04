"""Free-text job title -> NormalizedRole classification (config/roles.yaml
drives the patterns; see Stage: allowed normalized_role values).
"""

from __future__ import annotations

from src.config import AppConfig, get_config
from src.models import NormalizedRole
from src.processing.normalizer import normalize_title


class RoleClassifier:
    def __init__(self, config: AppConfig | None = None):
        self.config = config or get_config()
        self.patterns = self.config.title_patterns

    def classify(self, job_title: str | None) -> NormalizedRole:
        if not job_title:
            return NormalizedRole.OTHER
        normalized = normalize_title(job_title)
        if not normalized:
            return NormalizedRole.OTHER

        best_role: NormalizedRole | None = None
        best_len = -1
        for role_name, phrases in self.patterns.items():
            for phrase in phrases:
                if phrase in normalized and len(phrase) > best_len:
                    try:
                        role = NormalizedRole(role_name)
                    except ValueError:
                        continue
                    best_role = role
                    best_len = len(phrase)
        return best_role or NormalizedRole.OTHER

    def is_qualifying(self, role: NormalizedRole) -> bool:
        from src.models import QUALIFYING_ROLES

        return role in QUALIFYING_ROLES


_default_classifier: RoleClassifier | None = None


def classify_title(job_title: str | None) -> NormalizedRole:
    global _default_classifier
    if _default_classifier is None:
        _default_classifier = RoleClassifier()
    return _default_classifier.classify(job_title)
