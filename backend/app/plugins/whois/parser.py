"""Convert raw WHOIS data into structured analysis."""

from app.plugins.whois.schemas import WhoisParsedData, WhoisRawResponse
from app.plugins.whois.utils import days_until, is_unknown_registrar, privacy_is_enabled

_EXPIRY_WARNING_DAYS = 30


def parse(raw: WhoisRawResponse) -> WhoisParsedData:
    days_left = days_until(raw.expires)
    is_expired = days_left is not None and days_left < 0
    expiring_soon = days_left is not None and 0 <= days_left <= _EXPIRY_WARNING_DAYS
    privacy_enabled = privacy_is_enabled(text=raw.raw_text, registrant=raw.registrant, emails=raw.emails)
    privacy_disabled = privacy_enabled is False

    return WhoisParsedData(
        domain=raw.domain,
        registrar=raw.registrar,
        created=raw.created,
        updated=raw.updated,
        expires=raw.expires,
        name_servers=raw.name_servers,
        days_until_expiry=days_left,
        is_expired=is_expired,
        expiring_soon=expiring_soon,
        privacy_enabled=privacy_enabled,
        privacy_disabled=privacy_disabled,
        unknown_registrar=is_unknown_registrar(raw.registrar),
        query_error=raw.query_error,
    )
