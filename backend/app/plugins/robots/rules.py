from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.robots.schemas import RobotsParsedData


def evaluate_rules(parsed: RobotsParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    if parsed.admin_disallowed:
        return []

    return [
        scan_finding(
            plugin=plugin_id,
            rule_id="ROBOTS_ADMIN_DISALLOW_MISSING",
            asset_id=asset.asset_id,
            title="Admin Paths Not Disallowed",
            category="exposure",
            evidence="robots.txt does not disallow /admin",
            recommendation="Disallow sensitive paths in robots.txt or protect them with auth.",
            severity=FindingSeverity.MEDIUM,
            status=FindingCheckStatus.FAILED,
        )
    ]
