from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.future.kubernetes.schemas import KubernetesRawResponse, PodSpec


async def collect(asset: ScanTarget, options: ScanOptions) -> KubernetesRawResponse:
    return KubernetesRawResponse(
        cluster=asset.identifier,
        pods=[PodSpec(name="nginx", privileged=True)],
    )
