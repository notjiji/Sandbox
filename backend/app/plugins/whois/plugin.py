from datetime import UTC, datetime

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import FindingCheckStatus, ScanOptions, ScanResult, scan_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class WhoisPlugin(ScannerPlugin):
    id = "whois"
    name = "WHOIS Scanner"
    version = "1.0.0"
    supported_asset_types = ["domain", "email_domain"]
    supported_scan_types = [ScanType.FULL.value]
    default_config = PluginConfig(enabled=True, timeout=30.0, retries=1, parallel=False, version="1.0.0")

    async def run(self, asset: ScanTarget, options: ScanOptions) -> ScanResult:
        started_at = datetime.now(UTC)
        return ScanResult.success(
            plugin=self.id,
            version=self.version,
            started_at=started_at,
            findings=[
                scan_finding(
                    plugin=self.id,
                    rule_id="WHOIS_EXPIRING_SOON",
                    asset_id=asset.asset_id,
                    title="Domain Expiring Soon",
                    category="domain",
                    evidence="Registration expires in 21 days",
                    recommendation="Renew the domain registration before expiry.",
                    severity=FindingSeverity.LOW,
                    status=FindingCheckStatus.WARNING,
                ),
            ],
            metadata={"expires": "2026-08-24"},
        )
