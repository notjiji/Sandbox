from datetime import UTC, datetime

from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions, ScanResult
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.plugin import ScanTarget
from app.plugins.cookies import collector, parser, rules
from app.plugins.cookies.schemas import CookiesParsedData, CookiesRawResponse
from app.scans.enums import ScanType


class CookiesPlugin(ScannerPipeline[CookiesRawResponse, CookiesParsedData]):
    id = "cookies"
    name = "Cookie Security Scanner"
    version = "2.0.0"
    supported_asset_types = ["website", "api_endpoint"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]
    default_config = PluginConfig(enabled=True, timeout=20.0, retries=1, parallel=False, version="2.0.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> CookiesRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: CookiesRawResponse) -> CookiesParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: CookiesParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: CookiesParsedData) -> dict:
        return {
            "cookies": [
                {
                    "name": cookie.name,
                    "secure": cookie.secure,
                    "httponly": cookie.httponly,
                    "samesite": cookie.samesite,
                    "expires": cookie.expires,
                    "is_sensitive": cookie.is_sensitive,
                    "weak_name": cookie.weak_name,
                    "size_bytes": cookie.size_bytes,
                }
                for cookie in parsed.cookies
            ],
            "weak_name_cookies": parsed.weak_name_cookies,
            "cookie_count": parsed.cookie_count,
        }

    async def run(self, asset: ScanTarget, options: ScanOptions) -> ScanResult:
        started_at = datetime.now(UTC)
        raw = await self.collect(asset, options)
        parsed = self.parse(raw)
        findings = self.evaluate_rules(parsed, asset)
        return ScanResult.success(
            plugin=self.id,
            version=self.version,
            started_at=started_at,
            findings=findings,
            metadata=self.build_metadata(parsed),
        )
