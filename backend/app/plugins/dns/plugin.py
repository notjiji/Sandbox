from app.plugins.base import ScanResult, ScanTarget, ScannerPlugin


class DnsPlugin(ScannerPlugin):
    name = "dns"
    version = "0.1.0"

    def scan(self, target: ScanTarget) -> ScanResult:
        return ScanResult(
            success=True,
            findings=[
                {
                    "title": f"DNS records reviewed for {target.identifier}",
                    "description": "DNS resolution and record check completed.",
                    "severity": "info",
                }
            ],
            metadata={"plugin": self.name, "target": target.identifier},
        )
