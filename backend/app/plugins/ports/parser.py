"""Map raw port probes to structured service detections."""

from app.plugins.ports.banners import extract_from_banner
from app.plugins.ports.schemas import DetectedService, NmapServiceRaw, PortsParsedData, PortsRawResponse

_DEFAULT_SERVICE_BY_PORT = {
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "dns",
    80: "http",
    110: "pop3",
    143: "imap",
    443: "https",
    445: "smb",
    993: "imaps",
    995: "pop3s",
    3306: "mysql",
    3389: "rdp",
    5432: "postgresql",
    5900: "vnc",
    6379: "redis",
    8080: "http",
    8443: "https",
    8888: "http",
    9200: "elasticsearch",
    27017: "mongodb",
}


def _nmap_for_port(services: list[NmapServiceRaw], port: int) -> NmapServiceRaw | None:
    for service in services:
        if service.port == port:
            return service
    return None


def _detect_service(probe, nmap: NmapServiceRaw | None) -> DetectedService | None:
    if not probe.open:
        return None

    service_name, product, version = extract_from_banner(probe.port, probe.banner)
    service_name = service_name or _DEFAULT_SERVICE_BY_PORT.get(probe.port, "unknown")

    if nmap:
        if nmap.service_name:
            service_name = nmap.service_name
        if nmap.product:
            product = nmap.product
        if nmap.version:
            version = nmap.version
            if nmap.extrainfo:
                version = f"{version} {nmap.extrainfo}".strip()

    if probe.version and not version:
        version = probe.version

    if service_name == "ms-wbt-server":
        service_name = "rdp"
    if product and product.lower() == "openssh":
        service_name = "ssh"

    return DetectedService(
        port=probe.port,
        open=True,
        service=service_name,
        product=product,
        version=version,
        banner=probe.banner,
    )


def parse(raw: PortsRawResponse) -> PortsParsedData:
    services: list[DetectedService] = []
    for probe in raw.probes:
        detected = _detect_service(probe, _nmap_for_port(raw.nmap_services, probe.port))
        if detected is not None:
            services.append(detected)
    return PortsParsedData(host=raw.host, services=services)
