from app.shared.schemas.base import BaseSchema


class PortProbeRaw(BaseSchema):
    port: int
    open: bool = False
    service: str | None = None
    banner: str | None = None


class PortsRawResponse(BaseSchema):
    host: str
    probes: list[PortProbeRaw] = []


class PortsParsedData(BaseSchema):
    host: str
    open_ports: list[int]
    dangerous_ports: list[int]
    services: dict[int, str] = {}
    banners: dict[int, str] = {}
