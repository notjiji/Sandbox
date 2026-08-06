from datetime import UTC, datetime

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import FindingCheckStatus, ScanOptions, ScanResult, scan_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class CvePlugin(ScannerPlugin):
    id = "cve"
    name = "CVE Vulnerability Scanner"
    version = "0.1.0"
    supported_asset_types = [
        "server",
        "windows_server",
        "docker_host",
        "public_ip",
        "kubernetes_cluster",
    ]
    supported_scan_types = [ScanType.FULL.value, ScanType.CUSTOM.value]
    default_config = PluginConfig(enabled=False, timeout=180.0, retries=1, parallel=True, version="0.1.0")

    async def run(self, asset: ScanTarget, options: ScanOptions) -> ScanResult:
        started_at = datetime.now(UTC)
        return ScanResult.success(
            plugin=self.id,
            version=self.version,
            started_at=started_at,
            findings=[
                scan_finding(
                    plugin=self.id,
                    rule_id="CVE_KNOWN_VULNERABILITY",
                    asset_id=asset.asset_id,
                    title="Known CVE Detected",
                    description="A package with a published CVE is installed on the asset.",
                    category="vulnerability",
                    evidence="CVE-2024-0001 affects installed package openssl 1.1.1",
                    recommendation="Upgrade the affected package to a patched version.",
                    reference_links=["https://nvd.nist.gov/"],
                    cve="CVE-2024-0001",
                    cvss=7.5,
                    severity=FindingSeverity.HIGH,
                    status=FindingCheckStatus.FAILED,
                ),
            ],
            metadata={"preview": True, "cve_count": 1},
        )
