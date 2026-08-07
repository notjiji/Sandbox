from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.plugin import ScanTarget
from app.plugins.whois import collector, parser, rules
from app.plugins.whois.schemas import WhoisParsedData, WhoisRawResponse
from app.scans.enums import ScanType


class WhoisPlugin(ScannerPipeline[WhoisRawResponse, WhoisParsedData]):
    id = "whois"
    name = "WHOIS Scanner"
    version = "2.0.0"
    supported_asset_types = ["domain", "email_domain"]
    supported_scan_types = [ScanType.FULL.value]
    default_config = PluginConfig(enabled=True, timeout=30.0, retries=1, parallel=False, version="2.0.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> WhoisRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: WhoisRawResponse) -> WhoisParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: WhoisParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: WhoisParsedData) -> dict:
        return {
            "domain": parsed.domain,
            "registrar": parsed.registrar,
            "created": parsed.created.isoformat() if parsed.created else None,
            "updated": parsed.updated.isoformat() if parsed.updated else None,
            "expires": parsed.expires.isoformat() if parsed.expires else None,
            "name_servers": parsed.name_servers,
            "days_until_expiry": parsed.days_until_expiry,
            "privacy_enabled": parsed.privacy_enabled,
        }
