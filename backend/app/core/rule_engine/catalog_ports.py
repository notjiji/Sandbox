"""Declarative port exposure rules."""

from app.core.rule_engine.models import RuleSpec

PORTS_RULES: list[RuleSpec] = [
    RuleSpec(
        finding_code="PORT_FTP_OPEN",
        category="network",
        condition={"port_open": 21},
        evidence="{port_21_evidence}",
    ),
    RuleSpec(
        finding_code="PORT_TELNET_OPEN",
        category="network",
        condition={"port_open": 23},
        evidence="{port_23_evidence}",
    ),
    RuleSpec(
        finding_code="PORT_RDP_EXPOSED",
        category="network",
        condition={"port_open": 3389},
        evidence="{port_3389_evidence}",
    ),
    RuleSpec(
        finding_code="PORT_MYSQL_PUBLIC",
        category="network",
        condition={"port_open": 3306},
        evidence="{port_3306_evidence}",
    ),
    RuleSpec(
        finding_code="PORT_REDIS_PUBLIC",
        category="network",
        condition={"port_open": 6379},
        evidence="{port_6379_evidence}",
    ),
    RuleSpec(
        finding_code="PORT_MONGODB_PUBLIC",
        category="network",
        condition={"port_open": 27017},
        evidence="{port_27017_evidence}",
    ),
]
