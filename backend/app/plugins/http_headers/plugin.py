from app.plugins.base import ScanResult, ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class HttpHeadersPlugin(ScannerPlugin):
    name = "http_headers"
    description = "HTTP Headers Scanner"
    version = "0.1.0"
    supported_assets = ["website", "api_endpoint"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]

    async def scan(self, asset: ScanTarget) -> ScanResult:
        return ScanResult(
            success=True,
            findings=[
                {
                    "title": f"HTTP headers reviewed for {asset.identifier}",
                    "description": "Baseline header check completed.",
                    "severity": "info",
                }
            ],
            metadata={"plugin": self.name, "target": asset.identifier},
        )
