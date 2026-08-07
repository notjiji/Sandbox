"""Parse and validate security.txt content."""

from app.plugins.security_txt import validator
from app.plugins.security_txt.schemas import SecurityTxtParsedData, SecurityTxtRawResponse


def parse(raw: SecurityTxtRawResponse) -> SecurityTxtParsedData:
    if raw.error:
        return SecurityTxtParsedData(
            url=raw.url,
            final_url=raw.final_url,
            status_code=raw.status_code,
            present=False,
            error=raw.error,
        )

    present = raw.status_code == 200 and bool(raw.body.strip())
    if not present:
        return SecurityTxtParsedData(
            url=raw.url,
            final_url=raw.final_url,
            status_code=raw.status_code,
            present=False,
        )

    fields = validator.parse_fields(raw.body)
    return validator.validate_fields(fields, fetched_url=raw.url, final_url=raw.final_url)
