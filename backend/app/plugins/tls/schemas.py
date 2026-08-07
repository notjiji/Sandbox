from app.shared.schemas.base import BaseSchema


class TlsRawResponse(BaseSchema):
    host: str
    port: int = 443
    negotiated_cipher: str | None = None
    accepted_ciphers: list[str] = []
    weak_ciphers_accepted: list[str] = []
    protocol_probes: list[dict] = []
    connection_error: str | None = None


class TlsParsedData(BaseSchema):
    host: str
    port: int = 443
    min_version: str | None = None
    negotiated_cipher: str | None = None
    cipher_count: int = 0
    weak_cipher: bool = False
    weak_ciphers_accepted: list[str] = []
    legacy_protocols_accepted: list[str] = []
