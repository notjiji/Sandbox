import time

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.output import PluginFindingStatus, PluginOutput, report_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class CloudPlugin(ScannerPlugin):
    name = "cloud"
    description = "Cloud Posture Scanner (preview)"
    supported_assets = ["cloud_account", "s3_bucket", "azure_subscription"]
    supported_scan_types = [ScanType.FULL.value, ScanType.CUSTOM.value]
    default_config = PluginConfig(enabled=False, timeout=120.0, retries=1, parallel=False, version="0.1.0")

    async def scan(self, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        findings = [
            report_finding(
                plugin=self.name,
                code="CLOUD_PUBLIC_BUCKET",
                title="Public Storage Exposure",
                status=PluginFindingStatus.FAILED,
                evidence="Bucket policy allows public read",
                severity=FindingSeverity.CRITICAL,
            ),
        ]
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata={"preview": True},
        )
