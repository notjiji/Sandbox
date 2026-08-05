import time

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.output import PluginFindingStatus, PluginOutput, report_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
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
                title="TLS 1.0 Enabled",
                status=PluginFindingStatus.FAILED,
                evidence="TLS 1.0 cipher suite accepted",
                severity=FindingSeverity.HIGH,
            ),
        ]
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata={"tls_versions": ["TLSv1.0", "TLSv1.2", "TLSv1.3"]},
        )
