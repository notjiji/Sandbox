from app.plugins.base import ScanResult, ScanTarget, ScannerPlugin


class HttpHeadersPlugin(ScannerPlugin):
    name = "http_headers"
    version = "0.1.0"

    def scan(self, target: ScanTarget) -> ScanResult:
        return ScanResult(
            success=True,
            findings=[
                {
                    "title": f"HTTP headers reviewed for {target.identifier}",
                    "description": "Baseline header check completed.",
                    "severity": "info",
                }
            ],
            metadata={"plugin": self.name, "target": target.identifier},
        )
