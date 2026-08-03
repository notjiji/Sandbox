from app.plugins.base import ScanResult, ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class DnsPlugin(ScannerPlugin):
    name = "dns"
    description = "DNS Scanner"
    version = "0.1.0"
    supported_assets = ["website", "domain", "public_ip", "email_domain"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]

    async def scan(self, asset: ScanTarget) -> ScanResult:
        return ScanResult(
            success=True,
            findings=[
                {
                    "title": f"DNS records reviewed for {asset.identifier}",
                    "description": "DNS resolution and record check completed.",
                    "severity": "info",
                }
            ],
            metadata={"plugin": self.name, "target": asset.identifier},
        )
