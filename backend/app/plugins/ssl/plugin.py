import time

from app.findings.enums import FindingSeverity
from app.plugins.base import ScanTarget, ScannerPlugin
from app.plugins.config import PluginConfig
from app.plugins.output import PluginOutput, make_finding
from app.scans.enums import ScanType


class SslPlugin(ScannerPlugin):
    name = "ssl"
    description = "SSL Scanner"
    supported_assets = ["website", "domain", "api_endpoint", "email_domain"]
    supported_scan_types = [ScanType.FULL.value]
    default_config = PluginConfig(enabled=True, timeout=45.0, retries=2, parallel=False, version="0.1.0")

    async def scan(self, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        findings = [
            make_finding(
                plugin=self.name,
                title=f"TLS configuration reviewed for {asset.identifier}",
                description="Certificate and protocol check completed.",
                severity=FindingSeverity.LOW,
                evidence="Simulated certificate chain validated.",
                recommendation="Disable legacy TLS versions and enforce modern cipher suites.",
                references=["https://wiki.mozilla.org/Security/Server_Side_TLS"],
                raw_data={"tls_versions": ["TLSv1.2", "TLSv1.3"], "cipher": "TLS_AES_256_GCM_SHA384"},
                confidence=0.85,
            )
        ]
        metadata = {
            "certificate": asset.identifier,
            "issuer": "Let's Encrypt",
            "expires": "2026-12-31T23:59:59Z",
            "cipher": "TLS_AES_256_GCM_SHA384",
            "tls_versions": ["TLSv1.2", "TLSv1.3"],
        }
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata=metadata,
        )
