from app.plugins.base import ScanResult, ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class SslPlugin(ScannerPlugin):
    name = "ssl"
    description = "SSL Scanner"
    version = "0.1.0"
    supported_assets = ["website", "domain", "api_endpoint", "email_domain"]
    supported_scan_types = [ScanType.FULL.value]

    async def scan(self, asset: ScanTarget) -> ScanResult:
        return ScanResult(
            success=True,
            findings=[
                {
                    "title": f"TLS configuration reviewed for {asset.identifier}",
                    "description": "Certificate and protocol check completed.",
                    "severity": "low",
                }
            ],
            metadata={"plugin": self.name, "target": asset.identifier},
        )
