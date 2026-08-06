"""SSL scanner data models."""

from datetime import datetime

from app.shared.schemas.base import BaseSchema


class ProtocolProbeRaw(BaseSchema):
    version: str
    accepted: bool
    negotiated: str | None = None
    error: str | None = None


class CipherRaw(BaseSchema):
    name: str
    protocol: str
    secret_bits: int


class SslRawResponse(BaseSchema):
    """Raw TLS probe data — no findings."""

    host: str
    port: int
    certificate_b64: str | None = None
    getpeercert: dict = {}
    negotiated_cipher: CipherRaw | None = None
    protocol_probes: list[ProtocolProbeRaw] = []
    chain_trusted: bool = False
    ocsp_stapling: bool | None = None
    weak_ciphers_accepted: list[str] = []
    connection_error: str | None = None


class ParsedCertificate(BaseSchema):
    issuer: str
    subject: str
    common_name: str | None = None
    sans: list[str] = []
    not_before: datetime | None = None
    not_after: datetime | None = None
    is_expired: bool = False
    days_until_expiry: int | None = None
    is_wildcard: bool = False
    is_self_signed: bool = False
    signature_algorithm: str | None = None
    public_key_algorithm: str | None = None
    public_key_bits: int | None = None


class ParsedCipher(BaseSchema):
    name: str
    protocol: str
    secret_bits: int
    key_exchange: str | None = None
    forward_secrecy: bool = False


class SslParsedData(BaseSchema):
    host: str
    port: int
    protocols: list[str]
    protocols_accepted: list[str]
    certificate: ParsedCertificate
    cipher: ParsedCipher | None = None
    hostname_matches: bool = True
    chain_trusted: bool = False
    ocsp_stapling: bool | None = None
    weak_ciphers_accepted: list[str] = []
    san_covers_apex: bool = True
    san_covers_www: bool = True
    cipher_is_weak: bool = False
    lacks_forward_secrecy: bool = False

    @property
    def issuer(self) -> str:
        return self.certificate.issuer

    @property
    def expires(self) -> str:
        if self.certificate.not_after is None:
            return ""
        return self.certificate.not_after.isoformat()
