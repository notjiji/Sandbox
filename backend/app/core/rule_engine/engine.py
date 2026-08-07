"""Declarative rule engine — scanners ask: does this rule match?"""

from __future__ import annotations

from typing import Any

from app.core.rule_engine.catalog import get_plugin_rules
from app.core.rule_engine.conditions import matches
from app.core.rule_engine.context import build_context
from app.core.rule_engine.evidence import render_template
from app.core.rule_engine.models import RuleSpec
from app.plugins.base.contracts import ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget


def evaluate_rule(
    rule: RuleSpec,
    *,
    context: dict[str, Any],
    plugin_id: str,
    asset: ScanTarget,
) -> ScanFinding | None:
    if not matches(rule.condition, context):
        return None

    evidence = render_template(rule.evidence, context)
    title = rule.rule_code or rule.finding_code.replace("_", " ").title()

    return scan_finding(
        plugin=plugin_id,
        rule_id=rule.finding_code,
        asset_id=asset.asset_id,
        title=title,
        description=rule.description,
        category=rule.category,
        evidence=evidence or rule.finding_code,
        reference_links=list(rule.reference_links),
        status=rule.status,
    )


def evaluate_plugin_rules(
    plugin_id: str,
    parsed: Any,
    asset: ScanTarget,
    *,
    rules: list[RuleSpec] | None = None,
) -> list[ScanFinding]:
    """Evaluate all declarative rules for a plugin against parsed scan data."""
    rule_set = rules if rules is not None else get_plugin_rules(plugin_id)
    if not rule_set:
        return []

    context = build_context(parsed, asset, plugin_id=plugin_id)
    findings: list[ScanFinding] = []
    for rule in rule_set:
        finding = evaluate_rule(rule, context=context, plugin_id=plugin_id, asset=asset)
        if finding is not None:
            findings.append(finding)
    return findings
