import time

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.output import PluginFindingStatus, PluginOutput, report_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class KubernetesPlugin(ScannerPlugin):
    name = "kubernetes"
    description = "Kubernetes Security Scanner (preview)"
    supported_assets = ["kubernetes_cluster"]
    supported_scan_types = [ScanType.FULL.value, ScanType.CUSTOM.value]
    default_config = PluginConfig(enabled=False, timeout=120.0, retries=1, parallel=False, version="0.1.0")

    async def scan(self, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        findings = [
            report_finding(
                plugin=self.name,
                code="K8S_PRIVILEGED_POD",
                title="Privileged Pod Detected",
                status=PluginFindingStatus.FAILED,
                evidence="Pod nginx runs with privileged: true",
                severity=FindingSeverity.HIGH,
            ),
        ]
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata={"preview": True},
        )
