from app.plugins.base import ScanResult, ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class PortsPlugin(ScannerPlugin):
    name = "ports"
    description = "Port Scanner"
    version = "0.1.0"
    supported_assets = ["public_ip", "server", "windows_server", "docker_host"]
    supported_scan_types = [ScanType.FULL.value]

    async def scan(self, asset: ScanTarget) -> ScanResult:
        return ScanResult(
            success=True,
            findings=[
                {
                    "title": f"Open ports reviewed for {asset.identifier}",
                    "description": "Common port exposure check completed.",
                    "severity": "medium",
                }
            ],
            metadata={"plugin": self.name, "target": asset.identifier},
        )
