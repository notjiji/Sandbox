"""Declarative TLS cross-capability rules."""

from app.core.rule_engine.models import RuleSpec
from app.plugins.base.contracts import FindingCheckStatus

TLS_RULES: list[RuleSpec] = [
    RuleSpec(
        finding_code="TLS_NO_HSTS",
        category="transport",
        condition={"path_truthy": "tls_without_hsts"},
        evidence="TLS is enabled on {host} but no Strict-Transport-Security header was observed",
        description="HTTPS is deployed without HSTS, leaving users vulnerable to downgrade attacks.",
        status=FindingCheckStatus.WARNING,
    ),
]
