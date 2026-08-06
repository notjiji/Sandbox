from datetime import UTC, datetime

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import FindingCheckStatus, ScanOptions, ScanResult, scan_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class CloudPlugin(ScannerPlugin):
    id = "cloud"
    name = "Cloud Posture Scanner"
    version = "0.1.0"
    supported_asset_types = ["cloud_account", "s3_bucket", "azure_subscription"]
    supported_scan_types = [ScanType.FULL.value, ScanType.CUSTOM.value]
    default_config = PluginConfig(enabled=False, timeout=120.0, retries=1, parallel=False, version="0.1.0")

    async def run(self, asset: ScanTarget, options: ScanOptions) -> ScanResult:
        started_at = datetime.now(UTC)
        return ScanResult.success(
            plugin=self.id,
            version=self.version,
            started_at=started_at,
            findings=[
                scan_finding(
                    plugin=self.id,
                    rule_id="CLOUD_PUBLIC_BUCKET",
                    asset_id=asset.asset_id,
                    title="Public Storage Exposure",
                    category="cloud",
                    evidence="Bucket policy allows public read",
                    recommendation="Restrict bucket access to authorized principals only.",
                    severity=FindingSeverity.CRITICAL,
                    status=FindingCheckStatus.FAILED,
                ),
            ],
            metadata={"preview": True},
        )
