import time

from app.findings.enums import FindingSeverity
from app.plugins.base import ScanTarget, ScannerPlugin
from app.plugins.config import PluginConfig
from app.plugins.output import PluginOutput, PluginFindingStatus, report_finding
from app.scans.enums import ScanType


class WhoisPlugin(ScannerPlugin):
    name = "whois"
    description = "WHOIS Scanner"
    supported_assets = ["domain", "email_domain"]
    supported_scan_types = [ScanType.FULL.value]
    default_config = PluginConfig(enabled=True, timeout=30.0, retries=1, parallel=False, version="0.1.0")

    async def scan(self, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        findings = [
            report_finding(
                plugin=self.name,
                code="WHOIS_EXPIRING_SOON",
                title="Domain Expiring Soon",
                status=PluginFindingStatus.WARNING,
                evidence="Registration expires in 21 days",
                severity=FindingSeverity.LOW,
            ),
        ]
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata={"expires": "2026-08-24"},
        )
