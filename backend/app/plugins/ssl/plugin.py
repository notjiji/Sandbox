from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.plugin import ScanTarget
from app.plugins.ssl import collector, parser, rules
from app.plugins.ssl.schemas import SslParsedData, SslRawResponse
from app.scans.enums import ScanType


class SslPlugin(ScannerPipeline[SslRawResponse, SslParsedData]):
    id = "ssl"
    name = "SSL Scanner"
    version = "1.0.0"
    supported_asset_types = ["website", "domain", "api_endpoint", "email_domain"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=45.0, retries=2, parallel=False, version="1.0.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> SslRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: SslRawResponse) -> SslParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: SslParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: SslParsedData) -> dict:
        return {"tls_versions": parsed.protocols, "issuer": parsed.issuer, "expires": parsed.expires}
