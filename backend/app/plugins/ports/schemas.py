"""Port scanner data models."""

from app.shared.schemas.base import BaseSchema


class PortProbeRaw(BaseSchema):
    """Raw probe — collector output only."""

    port: int
    open: bool = False
    banner: str | None = None
    version: str | None = None


class NmapServiceRaw(BaseSchema):
    port: int
    protocol: str = "tcp"
    service_name: str | None = None
    product: str | None = None
    version: str | None = None
    extrainfo: str | None = None


class PortsRawResponse(BaseSchema):
    host: str
    probes: list[PortProbeRaw] = []
    nmap_services: list[NmapServiceRaw] = []
    nmap_used: bool = False


class DetectedService(BaseSchema):
    port: int
    open: bool = True
    service: str
    product: str | None = None
    version: str | None = None
    banner: str | None = None


class PortsParsedData(BaseSchema):
    host: str
    services: list[DetectedService] = []

    @property
    def open_ports(self) -> list[int]:
        return sorted(service.port for service in self.services if service.open)

    def has_open_port(self, port: int) -> bool:
        return any(service.port == port and service.open for service in self.services)

    def service_on_port(self, port: int) -> DetectedService | None:
        for service in self.services:
            if service.port == port and service.open:
                return service
        return None
