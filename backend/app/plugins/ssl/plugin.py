from datetime import UTC, datetime

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import FindingCheckStatus, ScanOptions, ScanResult, scan_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class SslPlugin(ScannerPlugin):
    id = "ssl"
    name = "SSL Scanner"
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
                    rule_id="SSL_TLS10_ENABLED",
                    asset_id=asset.asset_id,
                    title="TLS 1.0 Enabled",
                    description="The endpoint accepts deprecated TLS 1.0 connections.",
                    category="transport",
                    evidence="TLS 1.0 cipher suite accepted",
                    recommendation="Disable TLS 1.0 and enforce TLS 1.2 or higher.",
                    reference_links=["https://datatracker.ietf.org/doc/rfc8996/"],
                    severity=FindingSeverity.HIGH,
                    status=FindingCheckStatus.FAILED,
                ),
            ],
            metadata={"tls_versions": ["TLSv1.0", "TLSv1.2", "TLSv1.3"]},
        )
