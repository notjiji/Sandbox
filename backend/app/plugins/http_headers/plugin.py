from datetime import UTC, datetime

from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions, ScanResult
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.plugin import ScanTarget
from app.plugins.http_headers import collector, parser, rules
from app.plugins.http_headers.schemas import HttpHeadersParsedData, HttpHeadersRawResponse
from app.plugins.shared.scan_context import scan_context
from app.scans.enums import ScanType


class HttpHeadersPlugin(ScannerPipeline[HttpHeadersRawResponse, HttpHeadersParsedData]):
    id = "http_headers"
    name = "HTTP Scanner"
    version = "3.1.0"
    supported_asset_types = ["website", "api_endpoint"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=20.0, retries=1, parallel=False, version="3.1.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> HttpHeadersRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: HttpHeadersRawResponse) -> HttpHeadersParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: HttpHeadersParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: HttpHeadersParsedData) -> dict:
        return {
            "url": parsed.url,
            "final_url": parsed.final_url,
            "status_code": parsed.status_code,
            "content_type": parsed.content_type,
            "server": parsed.server,
            "redirect_count": len(parsed.redirects),
            "cookie_count": len(parsed.cookies),
            "timing_ms": parsed.timing.total_ms,
            "security_headers": parsed.security_headers.model_dump(exclude_none=True),
        }

    async def run(self, asset: ScanTarget, options: ScanOptions) -> ScanResult:
        started_at = datetime.now(UTC)
        raw = await self.collect(asset, options)
        parsed = self.parse(raw)
        scan_context.publish_transport_hints(
            {
                "has_hsts": parsed.has_hsts,
                "is_https": parsed.is_https,
            }
        )
        findings = self.evaluate_rules(parsed, asset)
        return ScanResult.success(
            plugin=self.id,
            version=self.version,
            started_at=started_at,
            findings=findings,
            metadata=self.build_metadata(parsed),
        )
