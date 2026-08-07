"""Parse collected HTTP data and detect technologies."""

from app.plugins.fingerprint import signatures
from app.plugins.fingerprint.schemas import FingerprintParsedData, FingerprintRawResponse


def parse(raw: FingerprintRawResponse) -> FingerprintParsedData:
    cookie_names = [cookie.name for cookie in raw.cookies]
    if raw.error:
        return FingerprintParsedData(
            url=raw.url,
            final_url=raw.final_url,
            status_code=raw.status_code,
            headers=raw.headers,
            cookie_names=cookie_names,
            script_srcs=raw.script_srcs,
            technologies=[],
            error=raw.error,
        )

    technologies = signatures.merge_technologies(
        signatures.detect_from_headers(raw.headers),
        signatures.detect_from_cookies(cookie_names),
        signatures.detect_from_scripts(raw.script_srcs),
        signatures.detect_from_html(raw.body),
    )

    return FingerprintParsedData(
        url=raw.url,
        final_url=raw.final_url,
        status_code=raw.status_code,
        headers=raw.headers,
        cookie_names=cookie_names,
        script_srcs=raw.script_srcs,
        technologies=technologies,
        error=None,
    )
