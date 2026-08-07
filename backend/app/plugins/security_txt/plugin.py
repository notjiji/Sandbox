from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.plugin import ScanTarget
from app.plugins.security_txt import collector, parser, rules
from app.plugins.security_txt.schemas import SecurityTxtParsedData, SecurityTxtRawResponse
from app.scans.enums import ScanType


class SecurityTxtPlugin(ScannerPipeline[SecurityTxtRawResponse, SecurityTxtParsedData]):
    id = "security_txt"
    name = "security.txt Scanner"
    version = "1.0.0"
    supported_asset_types = ["website", "domain", "api_endpoint"]
    supported_scan_types = [ScanType.FULL.value, ScanType.CUSTOM.value]
    default_config = PluginConfig(enabled=True, timeout=20.0, retries=1, parallel=False, version="1.0.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> SecurityTxtRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: SecurityTxtRawResponse) -> SecurityTxtParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: SecurityTxtParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: SecurityTxtParsedData) -> dict:
        return {
            "url": parsed.url,
            "final_url": parsed.final_url,
            "present": parsed.present,
            "status_code": parsed.status_code,
            "path": parsed.path,
            "contact": parsed.contacts,
            "encryption": parsed.encryption,
            "expires": parsed.expires,
            "expires_at": parsed.expires_at,
            "expires_valid": parsed.expires_valid,
            "expires_expired": parsed.expires_expired,
            "canonical": parsed.canonical,
            "canonical_matches": parsed.canonical_matches,
            "acknowledgments": parsed.acknowledgments,
            "policy": parsed.policy,
            "hiring": parsed.hiring,
            "preferred_languages": parsed.preferred_languages,
            "validation_issues": parsed.validation_issues,
            "field_validations": [item.model_dump() for item in parsed.field_validations],
            "error": parsed.error,
        }
