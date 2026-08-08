"""Declarative cookie security rules."""

from app.core.rule_engine.models import RuleSpec
from app.plugins.base.contracts import FindingCheckStatus

COOKIES_RULES: list[RuleSpec] = [
    RuleSpec(
        finding_code="COOKIE_MISSING_SECURE",
        category="cookies",
        condition={"path_nonempty": "cookies_missing_secure"},
        evidence="Cookies missing Secure flag: {missing_secure_evidence}",
    ),
    RuleSpec(
        finding_code="COOKIE_MISSING_HTTPONLY",
        category="cookies",
        condition={"path_nonempty": "cookies_missing_httponly"},
        evidence="Cookies accessible by JavaScript: {missing_httponly_evidence}",
    ),
    RuleSpec(
        finding_code="COOKIE_MISSING_SAMESITE",
        category="cookies",
        condition={"path_nonempty": "cookies_missing_samesite"},
        evidence="Cookies missing SameSite attribute: {missing_samesite_evidence}",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        finding_code="COOKIE_SENSITIVE_INSECURE",
        category="cookies",
        condition={"path_nonempty": "sensitive_insecure_cookies"},
        evidence="Sensitive cookies missing Secure or HttpOnly: {sensitive_insecure_evidence}",
    ),
    RuleSpec(
        finding_code="COOKIE_LONG_EXPIRATION",
        category="cookies",
        condition={"path_nonempty": "cookies_long_expiration"},
        evidence="Persistent cookies with long expiration: {long_expiration_evidence}",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        finding_code="COOKIE_OVERSIZED",
        category="cookies",
        condition={"path_nonempty": "cookies_oversized"},
        evidence="Cookies exceed recommended 4KB size: {oversized_evidence}",
    ),
    RuleSpec(
        finding_code="COOKIE_DUPLICATE",
        category="cookies",
        condition={"path_nonempty": "duplicate_names"},
        evidence="Duplicate cookie names detected: {duplicate_names_evidence}",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        finding_code="COOKIE_TOO_MANY",
        category="cookies",
        condition={"path_truthy": "has_too_many_cookies"},
        evidence="{cookie_count} Set-Cookie headers returned (recommended limit: 20)",
        status=FindingCheckStatus.WARNING,
    ),
]
