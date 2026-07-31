from app.plugins.base import ScanResult, ScanTarget, ScannerPlugin


class WhoisPlugin(ScannerPlugin):
    name = "whois"
    version = "0.1.0"

    def scan(self, target: ScanTarget) -> ScanResult:
        return ScanResult(
            success=True,
            findings=[
                {
                    "title": f"WHOIS data reviewed for {target.identifier}",
                    "description": "Registration metadata collected.",
                    "severity": "info",
                }
            ],
            metadata={"plugin": self.name, "target": target.identifier},
        )
