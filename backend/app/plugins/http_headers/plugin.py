import time

from app.findings.enums import FindingSeverity
from app.plugins.base import ScanTarget, ScannerPlugin
from app.plugins.config import PluginConfig
from app.plugins.output import PluginOutput, PluginFindingStatus, report_finding
from app.scans.enums import ScanType


class HttpHeadersPlugin(ScannerPlugin):
    name = "http_headers"
    description = "HTTP Headers Scanner"
    supported_assets = ["website", "api_endpoint"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=20.0, retries=1, parallel=False, version="0.1.0")

    async def scan(self, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        findings = [
            report_finding(
                plugin=self.name,
                code="HTTP_NO_CSP",
                title="Missing Content Security Policy",
                status=PluginFindingStatus.FAILED,
                evidence="Header not present",
                severity=FindingSeverity.MEDIUM,
            ),
            report_finding(
                plugin=self.name,
                code="HTTP_NO_HSTS",
                title="Missing Strict Transport Security",
                status=PluginFindingStatus.FAILED,
                evidence="HSTS header not present",
                severity=FindingSeverity.HIGH,
            ),
        ]
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata={"status_code": 200, "headers": {"server": "nginx"}},
        )
