from app.shared.schemas.base import BaseSchema


class DnsRawResponse(BaseSchema):
    domain: str
    records: dict[str, list[str]]


class DnsParsedData(BaseSchema):
    domain: str
    a_records: list[str]
    txt_records: list[str]
    has_spf: bool
