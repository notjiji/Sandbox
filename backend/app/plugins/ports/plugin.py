from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.plugin import ScanTarget
from app.plugins.ports import collector, parser, rules
from app.plugins.ports.schemas import PortsParsedData, PortsRawResponse
from app.scans.enums import ScanType


class PortsPlugin(ScannerPipeline[PortsRawResponse, PortsParsedData]):
    id = "ports"
    name = "Port Scanner"
    version = "3.0.0"
    supported_asset_types = ["public_ip", "server", "windows_server", "docker_host"]
    supported_scan_types = [ScanType.FULL.value]
    default_config = PluginConfig(enabled=True, timeout=90.0, retries=1, parallel=True, version="3.0.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> PortsRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: PortsRawResponse) -> PortsParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: PortsParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: PortsParsedData) -> dict:
        return {
            "open_ports": parsed.open_ports,
            "services": [
                {
                    "port": service.port,
                    "service": service.service,
                    "product": service.product,
                    "version": service.version,
                }
                for service in parsed.services
            ],
        }
