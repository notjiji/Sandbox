from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.plugin import ScanTarget
from app.plugins.future.cloud import collector, parser, rules
from app.plugins.future.cloud.schemas import CloudParsedData, CloudRawResponse
from app.scans.enums import ScanType


class CloudPlugin(ScannerPipeline[CloudRawResponse, CloudParsedData]):
    id = "cloud"
    name = "Cloud Posture Scanner"
    version = "0.1.0"
    supported_asset_types = ["cloud_account", "s3_bucket", "azure_subscription"]
    supported_scan_types = [ScanType.FULL.value, ScanType.CUSTOM.value]
    default_config = PluginConfig(enabled=False, timeout=120.0, retries=1, parallel=False, version="0.1.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> CloudRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: CloudRawResponse) -> CloudParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: CloudParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: CloudParsedData) -> dict:
        return {"preview": True}
