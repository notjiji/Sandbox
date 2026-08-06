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
    version = "3.0.0"
    supported_asset_types = ["website", "domain", "api_endpoint", "email_domain"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=45.0, retries=2, parallel=False, version="3.0.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> SslRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: SslRawResponse) -> SslParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: SslParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: SslParsedData) -> dict:
        cert = parsed.certificate
        metadata = {
            "host": parsed.host,
            "port": parsed.port,
            "protocols": parsed.protocols_accepted,
            "issuer": cert.issuer,
            "subject": cert.subject,
            "expires": cert.not_after.isoformat() if cert.not_after else None,
            "sans": cert.sans,
            "wildcard": cert.is_wildcard,
            "public_key_algorithm": cert.public_key_algorithm,
            "public_key_bits": cert.public_key_bits,
            "signature_algorithm": cert.signature_algorithm,
        }
        if parsed.cipher is not None:
            metadata["cipher"] = {
                "name": parsed.cipher.name,
                "protocol": parsed.cipher.protocol,
                "secret_bits": parsed.cipher.secret_bits,
                "key_exchange": parsed.cipher.key_exchange,
                "forward_secrecy": parsed.cipher.forward_secrecy,
            }
        return metadata
