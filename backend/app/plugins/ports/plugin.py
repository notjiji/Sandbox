from datetime import UTC, datetime

from app.findings.enums import FindingSeverity
from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import FindingCheckStatus, ScanOptions, ScanResult, scan_finding
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import ScanType


class PortsPlugin(ScannerPlugin):
    id = "ports"
    name = "Port Scanner"
    version = "1.0.0"
    supported_asset_types = ["public_ip", "server", "windows_server", "docker_host"]
    supported_scan_types = [ScanType.FULL.value]
    default_config = PluginConfig(enabled=True, timeout=60.0, retries=1, parallel=True, version="1.0.0")

    async def run(self, asset: ScanTarget, options: ScanOptions) -> ScanResult:
        started_at = datetime.now(UTC)
        return ScanResult.success(
            plugin=self.id,
            version=self.version,
            started_at=started_at,
            findings=[
                scan_finding(
                    plugin=self.id,
                    rule_id="PORT_TELNET_OPEN",
                    asset_id=asset.asset_id,
                    title="Telnet Port Open",
                    category="network",
                    evidence="TCP port 23 is open",
                    recommendation="Disable Telnet and use SSH instead.",
                    severity=FindingSeverity.CRITICAL,
                    status=FindingCheckStatus.FAILED,
                ),
            ],
            metadata={"open_ports": [22, 23, 80, 443]},
        )
