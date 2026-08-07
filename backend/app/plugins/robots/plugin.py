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
    version = "2.0.0"
    supported_asset_types = ["website", "domain", "api_endpoint"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=20.0, retries=1, parallel=False, version="2.0.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> RobotsRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: RobotsRawResponse) -> RobotsParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: RobotsParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: RobotsParsedData) -> dict:
        return {
            "url": parsed.url,
            "present": parsed.present,
            "status_code": parsed.status_code,
            "path": parsed.path,
            "rule_count": parsed.rule_count,
            "user_agents": parsed.user_agents,
            "disallowed_count": len(parsed.disallowed_paths),
            "allowed_count": len(parsed.allowed_paths),
            "sitemap_count": len(parsed.sitemaps),
            "disallowed_paths": [rule.path for rule in parsed.disallowed_paths[:30]],
            "allowed_paths": [rule.path for rule in parsed.allowed_paths[:30]],
            "sitemaps": parsed.sitemaps,
            "admin_paths": parsed.admin_paths,
            "debug_paths": parsed.debug_paths,
            "sensitive_paths": parsed.sensitive_paths,
            "matched_paths": [item.model_dump() for item in parsed.matched_paths[:30]],
            "error": parsed.error,
        }
