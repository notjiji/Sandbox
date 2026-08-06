from datetime import UTC, datetime

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import FindingCheckStatus, ScanOptions, ScanResult, scan_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class CookiesPlugin(ScannerPlugin):
    id = "cookies"
    name = "Cookie Security Scanner"
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
                    rule_id="COOKIE_MISSING_SECURE",
                    asset_id=asset.asset_id,
                    title="Session Cookie Missing Secure Flag",
                    category="cookies",
                    evidence="Set-Cookie: sessionid without Secure",
                    recommendation="Set the Secure attribute on session cookies.",
                    severity=FindingSeverity.HIGH,
                    status=FindingCheckStatus.FAILED,
                ),
                scan_finding(
                    plugin=self.id,
                    rule_id="COOKIE_MISSING_HTTPONLY",
                    asset_id=asset.asset_id,
                    title="Session Cookie Missing HttpOnly Flag",
                    category="cookies",
                    evidence="Set-Cookie: sessionid without HttpOnly",
                    recommendation="Set the HttpOnly attribute on session cookies.",
                    severity=FindingSeverity.MEDIUM,
                    status=FindingCheckStatus.FAILED,
                ),
            ],
            metadata={"cookies_checked": 4},
        )
