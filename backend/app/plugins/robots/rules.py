"""Robots.txt disclosure rules — sensitive paths listed in robots.txt."""

from collections.abc import Callable

from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.robots.schemas import RobotsParsedData

RuleFn = Callable[[RobotsParsedData, ScanTarget, str], ScanFinding | None]


def _format_paths(paths: list[str], *, limit: int = 5) -> str:
    shown = paths[:limit]
    suffix = f" (+{len(paths) - limit} more)" if len(paths) > limit else ""
    return ", ".join(shown) + suffix


def rule_admin_paths_disclosed(parsed: RobotsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.present or not parsed.admin_paths:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="ROBOTS_ADMIN_PATH_DISCLOSED",
        asset_id=asset.asset_id,
        title="Admin Paths Disclosed in robots.txt",
        category="exposure",
        evidence=f"Admin-related paths referenced in robots.txt: {_format_paths(parsed.admin_paths)}",
        recommendation=(
            "Remove sensitive path references from robots.txt. robots.txt is public and helps attackers "
            "discover hidden admin panels — protect admin areas with authentication instead."
        ),
        severity=FindingSeverity.MEDIUM,
        status=FindingCheckStatus.FAILED,
    )


def rule_debug_paths_disclosed(parsed: RobotsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.present or not parsed.debug_paths:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="ROBOTS_DEBUG_PATH_DISCLOSED",
        asset_id=asset.asset_id,
        title="Debug Paths Disclosed in robots.txt",
        category="exposure",
        evidence=f"Debug or test paths referenced in robots.txt: {_format_paths(parsed.debug_paths)}",
        recommendation=(
            "Remove debug and test path references from robots.txt and ensure debug endpoints are "
            "disabled or blocked in production."
        ),
        severity=FindingSeverity.HIGH,
        status=FindingCheckStatus.FAILED,
    )


def rule_sensitive_paths_disclosed(parsed: RobotsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.present or not parsed.sensitive_paths:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="ROBOTS_SENSITIVE_PATH_DISCLOSED",
        asset_id=asset.asset_id,
        title="Sensitive Paths Disclosed in robots.txt",
        category="exposure",
        evidence=f"Sensitive paths referenced in robots.txt: {_format_paths(parsed.sensitive_paths)}",
        recommendation=(
            "Avoid listing internal, backup, or configuration paths in robots.txt. Use access controls "
            "rather than robots rules to protect sensitive areas."
        ),
        severity=FindingSeverity.LOW,
        status=FindingCheckStatus.WARNING,
    )


RULES: list[RuleFn] = [
    rule_admin_paths_disclosed,
    rule_debug_paths_disclosed,
    rule_sensitive_paths_disclosed,
]


def evaluate_rules(parsed: RobotsParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    if not parsed.present:
        return []
    findings: list[ScanFinding] = []
    for rule in RULES:
        finding = rule(parsed, asset, plugin_id)
        if finding is not None:
            findings.append(finding)
    return findings
