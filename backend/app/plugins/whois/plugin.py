import time

from app.findings.enums import FindingSeverity
from app.plugins.base import ScanTarget, ScannerPlugin
from app.plugins.config import PluginConfig
from app.plugins.output import PluginOutput, make_finding
from app.scans.enums import ScanType


class WhoisPlugin(ScannerPlugin):
    name = "whois"
    description = "WHOIS Scanner"
    supported_assets = ["domain", "email_domain"]
    supported_scan_types = [ScanType.FULL.value]
    default_config = PluginConfig(enabled=True, timeout=25.0, retries=1, parallel=False, version="0.1.0")

    async def scan(self, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        findings = [
            make_finding(
                plugin=self.name,
                title=f"WHOIS data reviewed for {asset.identifier}",
                description="Registration metadata collected.",
                severity=FindingSeverity.INFO,
                evidence="Simulated WHOIS registry response.",
                recommendation="Monitor domain expiration dates and registrar changes.",
                raw_data={"registrar": "Example Registrar Inc.", "status": ["clientTransferProhibited"]},
                confidence=0.8,
            )
        ]
        metadata = {
            "registrar": "Example Registrar Inc.",
            "created": "2020-01-15T00:00:00Z",
            "updated": "2025-06-01T00:00:00Z",
            "expiration": "2027-01-15T00:00:00Z",
        }
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata=metadata,
        )
