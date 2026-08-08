"""TLS scanner — certificate, protocol, and cipher analysis."""

from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.plugin import ScanTarget
from app.plugins.ssl import collector, parser, rules
from app.plugins.ssl.schemas import SslParsedData, SslRawResponse
from app.scans.enums import ScanType


class TlsPlugin(ScannerPipeline[SslRawResponse, SslParsedData]):
    id = "tls"
    name = "TLS Scanner"
    version = "4.0.0"
    supported_asset_types = ["website", "domain", "api_endpoint", "email_domain"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=45.0, retries=2, parallel=False, version="4.0.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> SslRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: SslRawResponse) -> SslParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: SslParsedData, asset: ScanTarget):
        from app.core.rule_engine.engine import evaluate_plugin_rules

        return evaluate_plugin_rules(self.id, parsed, asset)

    def build_metadata(self, parsed: SslParsedData) -> dict:
        cert = parsed.certificate
        metadata = {
            "host": parsed.host,
            "port": parsed.port,
            "protocols": parsed.protocols_accepted,
            "issuer": cert.issuer,
            "subject": cert.subject,
            "common_name": cert.common_name,
            "serial_number": cert.serial_number,
            "fingerprint_sha256": cert.fingerprint_sha256,
            "expires": cert.not_after.isoformat() if cert.not_after else None,
            "days_until_expiry": cert.days_until_expiry,
            "sans": cert.sans,
            "wildcard": cert.is_wildcard,
            "public_key_algorithm": cert.public_key_algorithm,
            "public_key_bits": cert.public_key_bits,
            "signature_algorithm": cert.signature_algorithm,
            "chain_trusted": parsed.chain_trusted,
            "hostname_matches": parsed.hostname_matches,
            "ocsp_stapling": parsed.ocsp_stapling,
            "weak_ciphers_accepted": parsed.weak_ciphers_accepted,
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
