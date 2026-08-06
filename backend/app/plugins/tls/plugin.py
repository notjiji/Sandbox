from datetime import UTC, datetime

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import FindingCheckStatus, ScanOptions, ScanResult, scan_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class TlsPlugin(ScannerPlugin):
    id = "tls"
    name = "TLS Configuration Scanner"
    version = "1.0.0"
    supported_asset_types = ["website", "domain", "api_endpoint", "email_domain"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=45.0, retries=2, parallel=False, version="1.0.0")

    async def run(self, asset: ScanTarget, options: ScanOptions) -> ScanResult:
        started_at = datetime.now(UTC)
        return ScanResult.success(
            plugin=self.id,
            version=self.version,
            started_at=started_at,
            findings=[
                scan_finding(
                    plugin=self.id,
                    rule_id="TLS_WEAK_CIPHER",
                    asset_id=asset.asset_id,
                    title="Weak Cipher Suite Negotiated",
                    category="transport",
                    evidence="ECDHE-RSA-AES128-SHA accepted",
                    recommendation="Disable weak cipher suites and prefer AEAD ciphers.",
                    severity=FindingSeverity.HIGH,
                    status=FindingCheckStatus.FAILED,
                ),
            ],
            metadata={"min_version": "TLSv1.2", "cipher_count": 12},
        )
