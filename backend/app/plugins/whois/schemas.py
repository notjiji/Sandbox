"""WHOIS scanner data models."""

from datetime import datetime

from app.shared.schemas.base import BaseSchema


class WhoisRawResponse(BaseSchema):
    domain: str
    registrar: str | None = None
    created: datetime | None = None
    updated: datetime | None = None
    expires: datetime | None = None
    name_servers: list[str] = []
    registrant: str | None = None
    emails: list[str] = []
    raw_text: str | None = None
    query_error: str | None = None


class WhoisParsedData(BaseSchema):
    domain: str
    registrar: str | None = None
    created: datetime | None = None
    updated: datetime | None = None
    expires: datetime | None = None
    name_servers: list[str] = []
    days_until_expiry: int | None = None
    is_expired: bool = False
    expiring_soon: bool = False
    privacy_enabled: bool | None = None
    privacy_disabled: bool = False
    unknown_registrar: bool = False
    query_error: str | None = None
