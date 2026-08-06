from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.plugin import ScanTarget
from app.plugins.future.kubernetes import collector, parser, rules
from app.plugins.future.kubernetes.schemas import KubernetesParsedData, KubernetesRawResponse
from app.scans.enums import ScanType


class KubernetesPlugin(ScannerPipeline[KubernetesRawResponse, KubernetesParsedData]):
    id = "kubernetes"
    name = "Kubernetes Security Scanner"
    version = "0.1.0"
    supported_asset_types = ["kubernetes_cluster"]
    supported_scan_types = [ScanType.FULL.value, ScanType.CUSTOM.value]
    default_config = PluginConfig(enabled=False, timeout=120.0, retries=1, parallel=False, version="0.1.0")

    async def collect(self, asset: ScanTarget, options: ScanOptions) -> KubernetesRawResponse:
        return await collector.collect(asset, options)

    def parse(self, raw: KubernetesRawResponse) -> KubernetesParsedData:
        return parser.parse(raw)

    def evaluate_rules(self, parsed: KubernetesParsedData, asset: ScanTarget):
        return rules.evaluate_rules(parsed, asset, plugin_id=self.id)

    def build_metadata(self, parsed: KubernetesParsedData) -> dict:
        return {"preview": True}
