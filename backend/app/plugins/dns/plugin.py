from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.plugin import ScanTarget
from app.plugins.dns import collector, parser, rules
from app.plugins.dns.schemas import DnsParsedData, DnsRawResponse
from app.scans.enums import ScanType


class DnsPlugin(ScannerPipeline[DnsRawResponse, DnsParsedData]):
    id = "dns"
    name = "DNS Scanner"
    version = "1.0.0"
    supported_asset_types = ["website", "domain", "public_ip", "email_domain"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=30.0, retries=2, parallel=False, version="1.0.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> DnsRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: DnsRawResponse) -> DnsParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: DnsParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: DnsParsedData) -> dict:
        return {"records": {"A": parsed.a_records, "TXT": parsed.txt_records}}
