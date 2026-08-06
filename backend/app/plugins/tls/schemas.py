from app.shared.schemas.base import BaseSchema


class TlsRawResponse(BaseSchema):
    host: str
    negotiated_cipher: str
    min_version: str
    cipher_count: int


class TlsParsedData(BaseSchema):
    min_version: str
    negotiated_cipher: str
    cipher_count: int
    weak_cipher: bool
