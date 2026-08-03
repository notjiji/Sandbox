import time

from app.findings.enums import FindingSeverity
from app.plugins.base import ScanTarget, ScannerPlugin
from app.plugins.config import PluginConfig
from app.plugins.output import PluginOutput, make_finding
from app.scans.enums import ScanType


class PortsPlugin(ScannerPlugin):
    name = "ports"
    description = "Port Scanner"
    supported_assets = ["public_ip", "server", "windows_server", "docker_host"]
    supported_scan_types = [ScanType.FULL.value]
    default_config = PluginConfig(enabled=True, timeout=60.0, retries=0, parallel=True, version="0.1.0")

    async def scan(self, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        findings = [
            make_finding(
                plugin=self.name,
                title=f"Open ports reviewed for {asset.identifier}",
                description="Common port exposure check completed.",
                severity=FindingSeverity.MEDIUM,
                evidence="Simulated scan detected ports 22 and 443 open.",
                recommendation="Close unused ports and restrict administrative services by IP.",
                references=["https://www.cisa.gov/known-exploited-vulnerabilities-catalog"],
                raw_data={"open_ports": [22, 443], "filtered_ports": [3389]},
                confidence=0.88,
            )
        ]
        metadata = {
            "open_ports": [22, 443],
            "filtered_ports": [3389],
            "scan_profile": "common",
        }
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata=metadata,
        )
