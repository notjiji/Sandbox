from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.future.cloud.schemas import CloudParsedData


def evaluate_rules(parsed: CloudParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    if not parsed.public_read_allowed:
        return []

    return [
        scan_finding(
            plugin=plugin_id,
            rule_id="CLOUD_PUBLIC_BUCKET",
            asset_id=asset.asset_id,
            title="Public Storage Exposure",
            category="cloud",
            evidence="Bucket policy allows public read",
            recommendation="Restrict bucket access to authorized principals only.",
            severity=FindingSeverity.CRITICAL,
            status=FindingCheckStatus.FAILED,
        )
    ]
