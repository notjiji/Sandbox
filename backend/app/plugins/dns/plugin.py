from datetime import UTC, datetime

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import FindingCheckStatus, ScanOptions, ScanResult, scan_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class DnsPlugin(ScannerPlugin):
    id = "dns"
    name = "DNS Scanner"
    version = "1.0.0"
    supported_asset_types = ["website", "domain", "public_ip", "email_domain"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=30.0, retries=2, parallel=False, version="1.0.0")

    async def run(self, asset: ScanTarget, options: ScanOptions) -> ScanResult:
        started_at = datetime.now(UTC)
        return ScanResult.success(
            plugin=self.id,
            version=self.version,
            started_at=started_at,
            findings=[
                scan_finding(
                    plugin=self.id,
                    rule_id="DNS_MISSING_SPF",
                    asset_id=asset.asset_id,
                    title="Missing SPF Record",
                    description="No TXT record with SPF policy was found for the domain.",
                    category="dns",
                    evidence="No TXT record with SPF policy found",
                    recommendation="Publish an SPF TXT record to authorize sending mail servers.",
                    severity=FindingSeverity.MEDIUM,
                    status=FindingCheckStatus.FAILED,
                ),
            ],
            metadata={"records": {"A": ["203.0.113.10"]}},
        )
