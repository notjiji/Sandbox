"""Declarative TLS cipher/protocol rules."""

from app.core.rule_engine.models import RuleSpec
from app.plugins.base.contracts import FindingCheckStatus

TLS_RULES: list[RuleSpec] = [
    RuleSpec(
        finding_code="TLS_WEAK_CIPHER",
        category="transport",
        condition={"path_truthy": "weak_cipher"},
        evidence="{negotiated_cipher} accepted",
    ),
    RuleSpec(
        finding_code="TLS_LEGACY_PROTOCOL",
        category="transport",
        condition={"path_truthy": "legacy_protocol_enabled"},
        evidence="Legacy TLS protocols accepted: {legacy_protocols_evidence}",
    ),
    RuleSpec(
        finding_code="TLS_WEAK_CIPHERS_ACCEPTED",
        category="transport",
        condition={"path_nonempty": "weak_ciphers_accepted"},
        evidence="Server accepts weak cipher suites: {weak_ciphers_evidence}",
        status=FindingCheckStatus.WARNING,
    ),
]
