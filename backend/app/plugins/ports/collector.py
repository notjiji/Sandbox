import asyncio

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.ports.nmap_probe import nmap_available, scan_versions_nmap
from app.plugins.ports.scanner import merge_nmap_into_probes, resolve_host, scan_ports
from app.plugins.ports.schemas import PortsRawResponse


async def collect(asset: ScanTarget, options: ScanOptions) -> PortsRawResponse:
    host = resolve_host(asset.identifier)
    per_port_timeout = min(max(options.timeout / 25, 1.0), 5.0)

    probes = await scan_ports(host, timeout=per_port_timeout)
    open_ports = [probe.port for probe in probes if probe.open]

    nmap_services = []
    nmap_used = False
    if open_ports and nmap_available():
        nmap_services = await asyncio.to_thread(
            scan_versions_nmap,
            host,
            open_ports,
            options.timeout,
        )
        nmap_used = bool(nmap_services)
        probes = merge_nmap_into_probes(probes, nmap_services)

    return PortsRawResponse(
        host=host,
        probes=probes,
        nmap_services=nmap_services,
        nmap_used=nmap_used,
    )
