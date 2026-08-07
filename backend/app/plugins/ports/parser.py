from app.plugins.ports.schemas import PortsParsedData, PortsRawResponse

_DANGEROUS_PORTS = {21, 23, 445, 3389, 5900, 9200, 27017}


def parse(raw: PortsRawResponse) -> PortsParsedData:
    open_ports = [probe.port for probe in raw.probes if probe.open]
    dangerous = [port for port in open_ports if port in _DANGEROUS_PORTS]
    services = {probe.port: probe.service for probe in raw.probes if probe.open and probe.service}
    banners = {probe.port: probe.banner for probe in raw.probes if probe.open and probe.banner}
    return PortsParsedData(
        host=raw.host,
        open_ports=sorted(open_ports),
        dangerous_ports=sorted(dangerous),
        services=services,
        banners=banners,
    )
