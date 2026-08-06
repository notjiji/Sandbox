from app.shared.schemas.base import BaseSchema


class PortsRawResponse(BaseSchema):
    host: str
    open_ports: list[int]


class PortsParsedData(BaseSchema):
    host: str
    open_ports: list[int]
    dangerous_ports: list[int]
