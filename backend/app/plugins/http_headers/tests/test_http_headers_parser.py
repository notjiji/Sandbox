from app.plugins.http_headers.parser import parse
from app.plugins.http_headers.schemas import HttpHeadersRawResponse


def test_parse_detects_missing_security_headers() -> None:
    raw = HttpHeadersRawResponse(url="https://example.com", status_code=200, headers={"server": "nginx"})
    parsed = parse(raw)
    assert parsed.has_csp is False
    assert parsed.has_hsts is False
