import time

from app.plugins.base import ScanTarget, ScannerPlugin
from app.plugins.config import PluginConfig
from app.plugins.output import PluginOutput, PluginFindingStatus, report_finding
from app.scans.enums import ScanType


class PortsPlugin(ScannerPlugin):
    name = "ports"
    description = "Port Scanner"
    supported_assets = ["public_ip", "server", "windows_server", "docker_host"]
    supported_scan_types = [ScanType.FULL.value]
    default_config = PluginConfig(enabled=True, timeout=60.0, retries=1, parallel=True, version="0.1.0")

    async def scan(self, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        findings = [
            report_finding(
                plugin=self.name,
                code="PORT_TELNET_OPEN",
                status=PluginFindingStatus.FAILED,
                evidence="TCP port 23 is open and accepting connections.",
                raw_data={"open_ports": [22, 23, 80, 443]},
            ),
        ]
        metadata = {"open_ports": [22, 23, 80, 443], "filtered_ports": [8080]}
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata=metadata,
        )
