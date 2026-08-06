from app.plugins.http_headers.parser import parse
from app.plugins.http_headers.schemas import (
    HttpCookieRaw,
    HttpHeadersRawResponse,
    HttpProbeRaw,
    HttpRedirect,
    HttpTiming,
    HttpTraceProbeRaw,
)


def _probe(**kwargs) -> HttpProbeRaw:
    defaults = {
        "url": "https://example.com",
        "final_url": "https://example.com/",
        "status_code": 200,
        "headers": {"server": "nginx", "content-type": "text/html"},
        "cookies": [],
        "redirects": [],
        "body": "<html></html>",
        "body_length": 13,
        "content_type": "text/html",
        "timing": HttpTiming(total_ms=120.5, elapsed_ms=118.0),
    }
    defaults.update(kwargs)
    return HttpProbeRaw(**defaults)


def test_parse_extracts_security_headers_and_server() -> None:
    raw = HttpHeadersRawResponse(
        primary=_probe(
            headers={
                "server": "nginx/1.24",
                "x-powered-by": "Express",
                "content-type": "text/html; charset=utf-8",
            },
            content_type="text/html; charset=utf-8",
        ),
        http_probe=_probe(
            url="http://example.com",
            final_url="http://example.com/",
            status_code=301,
            headers={"location": "https://example.com/"},
        ),
        trace_probe=HttpTraceProbeRaw(url="https://example.com/", status_code=405, allowed=False),
    )

    parsed = parse(raw)

    assert parsed.server == "nginx/1.24"
    assert parsed.powered_by == "Express"
    assert parsed.content_type == "text/html; charset=utf-8"
    assert parsed.has_csp is False
    assert parsed.has_hsts is False
    assert parsed.http_redirects_to_https is True
    assert parsed.trace_enabled is False


def test_parse_detects_weak_session_cookies() -> None:
    raw = HttpHeadersRawResponse(
        primary=_probe(
            cookies=[
                HttpCookieRaw(name="sessionid", value="abc", secure=False, httponly=False),
            ]
        ),
    )

    parsed = parse(raw)

    assert len(parsed.weak_cookies) == 1
    assert parsed.weak_cookies[0].name == "sessionid"
