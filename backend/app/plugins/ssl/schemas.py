from app.shared.schemas.base import BaseSchema


class SslRawResponse(BaseSchema):
    """Raw TLS handshake and certificate data from the collector."""

    host: str
    port: int
    tls_versions_detected: list[str]
    certificate: dict


class SslParsedData(BaseSchema):
    """Structured SSL/TLS configuration."""

    protocols: list[str]
    issuer: str
    expires: str
    cipher_suites: list[str]
