from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.plugin import ScanTarget
from app.plugins.cookies import collector, parser, rules
from app.plugins.cookies.schemas import CookiesParsedData, CookiesRawResponse
from app.scans.enums import ScanType


class CookiesPlugin(ScannerPipeline[CookiesRawResponse, CookiesParsedData]):
    id = "cookies"
    name = "Cookie Security Scanner"
    version = "1.0.0"
    supported_asset_types = ["website", "api_endpoint"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=20.0, retries=1, parallel=False, version="1.0.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> CookiesRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: CookiesRawResponse) -> CookiesParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: CookiesParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: CookiesParsedData) -> dict:
        return {"cookies_checked": len(parsed.cookies)}
