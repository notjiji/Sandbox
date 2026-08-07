from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.plugin import ScanTarget
from app.plugins.fingerprint import collector, parser, rules
from app.plugins.fingerprint.schemas import FingerprintParsedData, FingerprintRawResponse
from app.scans.enums import ScanType


class FingerprintPlugin(ScannerPipeline[FingerprintRawResponse, FingerprintParsedData]):
    id = "fingerprint"
    name = "Technology Fingerprint Scanner"
    version = "1.0.0"
    supported_asset_types = ["website", "api_endpoint"]
    supported_scan_types = [ScanType.FULL.value, ScanType.CUSTOM.value]
    default_config = PluginConfig(enabled=True, timeout=25.0, retries=1, parallel=False, version="1.0.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> FingerprintRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: FingerprintRawResponse) -> FingerprintParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: FingerprintParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: FingerprintParsedData) -> dict:
        lower_map = {key.lower(): key for key in parsed.headers}
        picked_headers = {
            name: parsed.headers[lower_map[name.lower()]]
            for name in ("server", "x-powered-by", "cf-ray", "cf-cache-status", "via")
            if name in lower_map
        }
        return {
            "url": parsed.url,
            "final_url": parsed.final_url,
            "status_code": parsed.status_code,
            "technology_count": len(parsed.technologies),
            "technologies": [tech.model_dump() for tech in parsed.technologies],
            "script_count": len(parsed.script_srcs),
            "scripts": parsed.script_srcs[:20],
            "cookie_names": parsed.cookie_names,
            "headers": picked_headers,
            "error": parsed.error,
        }
