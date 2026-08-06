from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.whois.schemas import WhoisParsedData


def evaluate_rules(parsed: WhoisParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    if not parsed.expiring_soon:
        return []

    return [
        scan_finding(
            plugin=plugin_id,
            rule_id="WHOIS_EXPIRING_SOON",
            asset_id=asset.asset_id,
            title="Domain Expiring Soon",
            category="domain",
            evidence=f"Registration expires in {parsed.days_until_expiry} days",
            recommendation="Renew the domain registration before expiry.",
            severity=FindingSeverity.LOW,
            status=FindingCheckStatus.WARNING,
        )
    ]
