from app.plugins.whois.schemas import WhoisParsedData, WhoisRawResponse

_EXPIRY_WARNING_DAYS = 30


def parse(raw: WhoisRawResponse) -> WhoisParsedData:
    return WhoisParsedData(
        domain=raw.domain,
        expires=raw.expires,
        days_until_expiry=raw.days_until_expiry,
        expiring_soon=raw.days_until_expiry <= _EXPIRY_WARNING_DAYS,
    )
