"""Declarative cloud posture rules."""

from app.core.rule_engine.models import RuleSpec

CLOUD_RULES: list[RuleSpec] = [
    RuleSpec(
        finding_code="CLOUD_PUBLIC_BUCKET",
        category="cloud",
        condition={"path_truthy": "public_read_allowed"},
        evidence="Bucket policy allows public read for {resource_id}",
    ),
]
