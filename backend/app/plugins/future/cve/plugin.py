from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.plugin import ScanTarget
from app.plugins.future.cve import collector, parser, rules
from app.plugins.future.cve.schemas import CveParsedData, CveRawResponse
from app.scans.enums import ScanType


class CvePlugin(ScannerPipeline[CveRawResponse, CveParsedData]):
    id = "cve"
    name = "CVE Vulnerability Scanner"
    version = "1.0.0"
    supported_asset_types = [
        "server",
        "windows_server",
        "docker_host",
        "public_ip",
        "kubernetes_cluster",
        "website",
        "api_endpoint",
    ]
    supported_scan_types = [ScanType.FULL.value, ScanType.CUSTOM.value]
    default_config = PluginConfig(enabled=True, timeout=180.0, retries=1, parallel=True, version="1.0.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> CveRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: CveRawResponse) -> CveParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: CveParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: CveParsedData) -> dict:
        return {"preview": False, "cve_count": len(parsed.vulnerable_packages)}
