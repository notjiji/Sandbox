from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.ports.schemas import PortsRawResponse


async def collect(asset: ScanTarget, options: ScanOptions) -> PortsRawResponse:
    return PortsRawResponse(host=asset.identifier, open_ports=[22, 23, 80, 443])
