from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.plugin import ScanTarget
from app.plugins.http_headers import collector, parser, rules
from app.plugins.http_headers.schemas import HttpHeadersParsedData, HttpHeadersRawResponse
from app.scans.enums import ScanType


class HttpHeadersPlugin(ScannerPipeline[HttpHeadersRawResponse, HttpHeadersParsedData]):
    id = "http_headers"
    name = "HTTP Headers Scanner"
    version = "1.0.0"
    supported_asset_types = ["website", "api_endpoint"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=20.0, retries=1, parallel=False, version="1.0.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> HttpHeadersRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: HttpHeadersRawResponse) -> HttpHeadersParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: HttpHeadersParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: HttpHeadersParsedData) -> dict:
        return {"status_code": parsed.status_code, "headers": parsed.headers}
