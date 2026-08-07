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
    version = "3.1.0"
    supported_asset_types = ["website", "domain", "public_ip", "email_domain"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=30.0, retries=2, parallel=False, version="3.1.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> DnsRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: DnsRawResponse) -> DnsParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: DnsParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: DnsParsedData) -> dict:
        return {
            "domain": parsed.domain,
            "records": {
                "A": parsed.a_records,
                "AAAA": parsed.aaaa_records,
                "MX": parsed.mx_records,
                "TXT": parsed.txt_records,
                "NS": parsed.ns_records,
                "SOA": [parsed.soa_record] if parsed.soa_record else [],
                "CNAME": parsed.cname_records,
            },
            "spf": parsed.spf_record,
            "spf_records": parsed.spf_records,
            "dmarc": parsed.dmarc_record,
            "dmarc_policy": parsed.dmarc_policy,
            "dkim_selectors": parsed.dkim_selectors_found,
            "dnssec_enabled": parsed.dnssec_enabled,
            "dnssec_incomplete": parsed.dnssec_incomplete,
            "caa": parsed.caa_records,
            "mta_sts": parsed.mta_sts_present,
            "tls_rpt": parsed.tls_rpt_present,
            "bimi": parsed.bimi_present,
            "wildcard_detected": parsed.wildcard_detected,
            "subdomain_takeover_risks": parsed.subdomain_takeover_risks,
            "zone_transfer_allowed": parsed.zone_transfer_allowed,
            "minimum_ttl": parsed.minimum_ttl,
        }
