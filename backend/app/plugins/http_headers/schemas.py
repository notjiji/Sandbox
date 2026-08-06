from app.shared.schemas.base import BaseSchema


class HttpHeadersRawResponse(BaseSchema):
    url: str
    status_code: int
    headers: dict[str, str]


class HttpHeadersParsedData(BaseSchema):
    status_code: int
    headers: dict[str, str]
    has_csp: bool
    has_hsts: bool
