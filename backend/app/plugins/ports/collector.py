import asyncio

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.ports.scanner import resolve_host, scan_ports
from app.plugins.ports.schemas import PortsRawResponse


async def collect(asset: ScanTarget, options: ScanOptions) -> PortsRawResponse:
    host = resolve_host(asset.identifier)
    per_port_timeout = min(max(options.timeout / 20, 1.0), 5.0)
    probes = await scan_ports(host, timeout=per_port_timeout)
    return PortsRawResponse(host=host, probes=probes)
