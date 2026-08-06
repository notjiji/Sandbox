from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.plugin import ScanTarget
from app.plugins.robots import collector, parser, rules
from app.plugins.robots.schemas import RobotsParsedData, RobotsRawResponse
from app.scans.enums import ScanType


class RobotsPlugin(ScannerPipeline[RobotsRawResponse, RobotsParsedData]):
    id = "robots"
    name = "Robots.txt Scanner"
    version = "1.0.0"
    supported_asset_types = ["website", "domain", "api_endpoint"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=20.0, retries=1, parallel=False, version="1.0.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> RobotsRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: RobotsRawResponse) -> RobotsParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: RobotsParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: RobotsParsedData) -> dict:
        return {"path": parsed.path, "rules": parsed.rule_count}
