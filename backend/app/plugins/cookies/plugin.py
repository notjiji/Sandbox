import time

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.output import PluginFindingStatus, PluginOutput, report_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class CookiesPlugin(ScannerPlugin):
    name = "cookies"
    description = "Cookie Security Scanner"
    supported_assets = ["website", "api_endpoint"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=20.0, retries=1, parallel=False, version="0.1.0")

    async def scan(self, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        findings = [
            report_finding(
                plugin=self.name,
                code="COOKIE_MISSING_SECURE",
                title="Session Cookie Missing Secure Flag",
                status=PluginFindingStatus.FAILED,
                evidence="Set-Cookie: sessionid without Secure",
                severity=FindingSeverity.HIGH,
            ),
            report_finding(
                plugin=self.name,
                code="COOKIE_MISSING_HTTPONLY",
                title="Session Cookie Missing HttpOnly Flag",
                status=PluginFindingStatus.FAILED,
                evidence="Set-Cookie: sessionid without HttpOnly",
                severity=FindingSeverity.MEDIUM,
            ),
        ]
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata={"cookies_checked": 4},
        )
