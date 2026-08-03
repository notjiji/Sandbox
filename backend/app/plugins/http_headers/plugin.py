import time

from app.findings.enums import FindingSeverity
from app.plugins.base import ScanTarget, ScannerPlugin
from app.plugins.config import PluginConfig
from app.plugins.output import PluginOutput, make_finding
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
            make_finding(
                plugin=self.name,
                title=f"HTTP headers reviewed for {asset.identifier}",
                description="Baseline header check completed.",
                severity=FindingSeverity.INFO,
                evidence="Simulated response headers captured.",
                recommendation="Review security headers such as CSP and HSTS.",
                references=["https://owasp.org/www-project-secure-headers/"],
                raw_data={"status_code": 200, "headers": {"server": "nginx"}, "redirect_count": 0},
                confidence=0.9,
            )
        ]
        metadata = {
            "status_code": 200,
            "headers": {"server": "nginx", "x-frame-options": "SAMEORIGIN"},
            "redirect_count": 0,
        }
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata=metadata,
        )
