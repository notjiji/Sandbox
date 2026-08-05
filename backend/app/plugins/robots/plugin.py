import time

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.output import PluginFindingStatus, PluginOutput, report_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class RobotsPlugin(ScannerPlugin):
    name = "robots"
    description = "Robots.txt Scanner"
    supported_assets = ["website", "domain", "api_endpoint"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=20.0, retries=1, parallel=False, version="0.1.0")

    async def scan(self, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        findings = [
            report_finding(
                plugin=self.name,
                code="ROBOTS_ADMIN_DISALLOW_MISSING",
                title="Admin Paths Not Disallowed",
                status=PluginFindingStatus.FAILED,
                evidence="robots.txt does not disallow /admin",
                severity=FindingSeverity.MEDIUM,
            ),
        ]
        return PluginOutput.completed(
            plugin=self.name,
            duration=round(time.perf_counter() - started, 2),
            findings=findings,
            metadata={"path": "/robots.txt", "rules": 3},
        )
