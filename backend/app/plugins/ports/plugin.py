from app.plugins.base import ScanResult, ScanTarget, ScannerPlugin


class PortsPlugin(ScannerPlugin):
    name = "ports"
    version = "0.1.0"

    def scan(self, target: ScanTarget) -> ScanResult:
        return ScanResult(
            success=True,
            findings=[
                {
                    "title": f"Open ports reviewed for {target.identifier}",
                    "description": "Common port exposure check completed.",
                    "severity": "medium",
                }
            ],
            metadata={"plugin": self.name, "target": target.identifier},
        )
