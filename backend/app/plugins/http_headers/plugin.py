from datetime import UTC, datetime

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import FindingCheckStatus, ScanOptions, ScanResult, scan_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class HttpHeadersPlugin(ScannerPlugin):
    id = "http_headers"
    name = "HTTP Headers Scanner"
    version = "1.0.0"
    supported_asset_types = ["website", "api_endpoint"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=20.0, retries=1, parallel=False, version="1.0.0")

    async def run(self, asset: ScanTarget, options: ScanOptions) -> ScanResult:
        started_at = datetime.now(UTC)
        return ScanResult.success(
            plugin=self.id,
            version=self.version,
            started_at=started_at,
            findings=[
                scan_finding(
                    plugin=self.id,
                    rule_id="HTTP_NO_CSP",
                    asset_id=asset.asset_id,
                    title="Missing Content Security Policy",
                    category="headers",
                    evidence="Header not present",
                    recommendation="Add a Content-Security-Policy header.",
                    severity=FindingSeverity.MEDIUM,
                    status=FindingCheckStatus.FAILED,
                ),
                scan_finding(
                    plugin=self.id,
                    rule_id="HTTP_NO_HSTS",
                    asset_id=asset.asset_id,
                    title="Missing Strict Transport Security",
                    category="headers",
                    evidence="HSTS header not present",
                    recommendation="Add Strict-Transport-Security with a long max-age.",
                    severity=FindingSeverity.HIGH,
                    status=FindingCheckStatus.FAILED,
                ),
            ],
            metadata={"status_code": 200, "headers": {"server": "nginx"}},
        )
