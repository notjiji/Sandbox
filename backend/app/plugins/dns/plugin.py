import time

from app.findings.enums import FindingSeverity
from app.plugins.base import ScanTarget, ScannerPlugin
from app.plugins.config import PluginConfig
from app.plugins.output import PluginOutput, make_finding
from app.scans.enums import ScanType


class DnsPlugin(ScannerPlugin):
    name = "dns"
    description = "DNS Scanner"
    supported_assets = ["website", "domain", "public_ip", "email_domain"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=15.0, retries=2, parallel=True, version="0.1.0")

    async def scan(self, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        findings = [
            make_finding(
                plugin=self.name,
                title=f"DNS records reviewed for {asset.identifier}",
                description="DNS resolution and record check completed.",
                severity=FindingSeverity.INFO,
                evidence="Simulated A/AAAA/MX records resolved.",
                recommendation="Verify SPF, DKIM, and DMARC for mail-related assets.",
                raw_data={"records": {"A": ["203.0.113.10"], "MX": ["mail.example.com"]}},
                confidence=0.95,
            )
        ]
        metadata = {
            "records": {"A": ["203.0.113.10"], "AAAA": [], "MX": ["mail.example.com"]},
            "resolver": "system",
        }
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata=metadata,
        )
