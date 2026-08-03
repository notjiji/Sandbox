import time

from app.plugins.base import ScanTarget, ScannerPlugin
from app.plugins.config import PluginConfig
from app.plugins.output import PluginOutput, PluginFindingStatus, report_finding
from app.scans.enums import ScanType


class DnsPlugin(ScannerPlugin):
    name = "dns"
    description = "DNS Scanner"
    supported_assets = ["website", "domain", "public_ip", "email_domain"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=30.0, retries=2, parallel=False, version="0.1.0")

    async def scan(self, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        findings = [
            report_finding(
                plugin=self.name,
                code="DNS_MISSING_SPF",
                status=PluginFindingStatus.FAILED,
                evidence="No TXT record with SPF policy found.",
                raw_data={"records": {"A": ["203.0.113.10"], "MX": ["mail.example.com"]}},
            ),
        ]
        metadata = {"records": {"A": ["203.0.113.10"], "MX": ["mail.example.com"]}}
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata=metadata,
        )
