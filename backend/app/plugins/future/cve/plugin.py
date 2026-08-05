import time

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.output import PluginFindingStatus, PluginOutput, report_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class CvePlugin(ScannerPlugin):
    name = "cve"
    description = "CVE Vulnerability Scanner (preview)"
    supported_assets = [
        "server",
        "windows_server",
        "docker_host",
        "public_ip",
        "kubernetes_cluster",
    ]
    supported_scan_types = [ScanType.FULL.value, ScanType.CUSTOM.value]
    default_config = PluginConfig(enabled=False, timeout=180.0, retries=1, parallel=True, version="0.1.0")

    async def scan(self, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        findings = [
            report_finding(
                plugin=self.name,
                code="CVE_KNOWN_VULNERABILITY",
                title="Known CVE Detected",
                status=PluginFindingStatus.FAILED,
                evidence="CVE-2024-0001 affects installed package openssl 1.1.1",
                severity=FindingSeverity.HIGH,
            ),
        ]
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata={"preview": True, "cve_count": 1},
        )
