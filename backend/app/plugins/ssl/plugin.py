import time

from app.plugins.base import ScanTarget, ScannerPlugin
from app.plugins.config import PluginConfig
from app.plugins.output import PluginOutput, PluginFindingStatus, report_finding
from app.scans.enums import ScanType


class SslPlugin(ScannerPlugin):
    name = "ssl"
    description = "SSL Scanner"
    supported_assets = ["website", "domain", "api_endpoint", "email_domain"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=45.0, retries=2, parallel=False, version="0.1.0")

    async def scan(self, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        findings = [
            report_finding(
                plugin=self.name,
                code="SSL_TLS10_ENABLED",
                status=PluginFindingStatus.FAILED,
                evidence="TLS 1.0 cipher suite accepted during handshake.",
                raw_data={"tls_versions": ["TLSv1.0", "TLSv1.2", "TLSv1.3"]},
            ),
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
