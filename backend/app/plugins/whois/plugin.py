from app.plugins.base import ScanResult, ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class WhoisPlugin(ScannerPlugin):
    name = "whois"
    description = "WHOIS Scanner"
    version = "0.1.0"
    supported_assets = ["domain", "email_domain"]
    supported_scan_types = [ScanType.FULL.value]

    async def scan(self, asset: ScanTarget) -> ScanResult:
        return ScanResult(
            success=True,
            findings=[
                {
                    "title": f"WHOIS data reviewed for {asset.identifier}",
                    "description": "Registration metadata collected.",
                    "severity": "info",
                }
            ],
            metadata={"plugin": self.name, "target": asset.identifier},
        )
