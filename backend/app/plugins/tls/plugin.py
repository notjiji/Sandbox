import time

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.output import PluginFindingStatus, PluginOutput, report_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class TlsPlugin(ScannerPlugin):
    name = "tls"
    description = "TLS Configuration Scanner"
    supported_assets = ["website", "domain", "api_endpoint", "email_domain"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=45.0, retries=2, parallel=False, version="0.1.0")

    async def scan(self, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        findings = [
            report_finding(
                plugin=self.name,
                code="TLS_WEAK_CIPHER",
                title="Weak Cipher Suite Negotiated",
                status=PluginFindingStatus.FAILED,
                evidence="ECDHE-RSA-AES128-SHA accepted",
                severity=FindingSeverity.HIGH,
            ),
        ]
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata={"min_version": "TLSv1.2", "cipher_count": 12},
        )
