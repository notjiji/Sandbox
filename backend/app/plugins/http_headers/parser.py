from app.plugins.http_headers.schemas import HttpHeadersParsedData, HttpHeadersRawResponse


def _header_present(headers: dict[str, str], name: str) -> bool:
    lower = name.lower()
    return any(key.lower() == lower for key in headers)


def parse(raw: HttpHeadersRawResponse) -> HttpHeadersParsedData:
    return HttpHeadersParsedData(
        status_code=raw.status_code,
        headers=raw.headers,
        has_csp=_header_present(raw.headers, "content-security-policy"),
        has_hsts=_header_present(raw.headers, "strict-transport-security"),
    )
