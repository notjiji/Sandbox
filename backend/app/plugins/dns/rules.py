from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.dns.schemas import DnsParsedData


def evaluate_rules(parsed: DnsParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    if parsed.has_spf:
        return []

    return [
        scan_finding(
            plugin=plugin_id,
            rule_id="DNS_MISSING_SPF",
            asset_id=asset.asset_id,
            title="Missing SPF Record",
            description="No TXT record with SPF policy was found for the domain.",
            category="dns",
            evidence="No TXT record with SPF policy found",
            recommendation="Publish an SPF TXT record to authorize sending mail servers.",
            severity=FindingSeverity.MEDIUM,
            status=FindingCheckStatus.FAILED,
        )
    ]
