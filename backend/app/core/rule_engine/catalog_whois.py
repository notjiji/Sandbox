"""Declarative WHOIS rules."""

from app.core.rule_engine.models import RuleSpec
from app.plugins.base.contracts import FindingCheckStatus

WHOIS_RULES: list[RuleSpec] = [
    RuleSpec(
        finding_code="WHOIS_EXPIRED",
        category="domain",
        condition={"path_truthy": "is_expired"},
        evidence="WHOIS expiration date: {expires_evidence}",
    ),
    RuleSpec(
        finding_code="WHOIS_EXPIRING_SOON",
        category="domain",
        condition={
            "op": "and",
            "conditions": [
                {"path_falsy": "is_expired"},
                {"path_truthy": "expiring_soon"},
                {"op": "truthy", "path": "days_until_expiry"},
            ],
        },
        evidence="Registration expires in {days_until_expiry} days",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        finding_code="WHOIS_PRIVACY_DISABLED",
        category="domain",
        condition={"path_truthy": "privacy_disabled"},
        evidence="Registrant contact details appear publicly visible in WHOIS",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        finding_code="WHOIS_UNKNOWN_REGISTRAR",
        category="domain",
        condition={"path_truthy": "unknown_registrar"},
        evidence="Registrar field missing or unknown for {domain}",
        status=FindingCheckStatus.WARNING,
    ),
]
