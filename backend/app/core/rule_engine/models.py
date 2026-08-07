"""Rule specification models."""

from dataclasses import dataclass, field

from app.plugins.base.contracts import FindingCheckStatus


@dataclass(frozen=True)
class RuleSpec:
    """Declarative rule: condition match → finding (metadata from risk_rules DB)."""

    finding_code: str
    condition: dict
    rule_code: str | None = None
    category: str = "general"
    evidence: str = "{finding_code} matched on {identifier}"
    description: str | None = None
    status: FindingCheckStatus = FindingCheckStatus.FAILED
    reference_links: tuple[str, ...] = field(default_factory=tuple)
