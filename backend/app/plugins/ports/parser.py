from app.plugins.ports.schemas import PortsParsedData, PortsRawResponse

_DANGEROUS_PORTS = {21, 23, 445, 3389}


def parse(raw: PortsRawResponse) -> PortsParsedData:
    dangerous = [port for port in raw.open_ports if port in _DANGEROUS_PORTS]
    return PortsParsedData(host=raw.host, open_ports=raw.open_ports, dangerous_ports=dangerous)
