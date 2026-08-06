from datetime import UTC, datetime

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import FindingCheckStatus, ScanOptions, ScanResult, scan_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class RobotsPlugin(ScannerPlugin):
    id = "robots"
    name = "Robots.txt Scanner"
    version = "1.0.0"
    supported_asset_types = ["website", "domain", "api_endpoint"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=20.0, retries=1, parallel=False, version="1.0.0")

    async def run(self, asset: ScanTarget, options: ScanOptions) -> ScanResult:
        started_at = datetime.now(UTC)
        return ScanResult.success(
            plugin=self.id,
            version=self.version,
            started_at=started_at,
            findings=[
                scan_finding(
                    plugin=self.id,
                    rule_id="ROBOTS_ADMIN_DISALLOW_MISSING",
                    asset_id=asset.asset_id,
                    title="Admin Paths Not Disallowed",
                    category="exposure",
                    evidence="robots.txt does not disallow /admin",
                    recommendation="Disallow sensitive paths in robots.txt or protect them with auth.",
                    severity=FindingSeverity.MEDIUM,
                    status=FindingCheckStatus.FAILED,
                ),
            ],
            metadata={"path": "/robots.txt", "rules": 3},
        )
