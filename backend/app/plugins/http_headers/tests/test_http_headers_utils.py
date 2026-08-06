from app.plugins.http_headers.utils import (
    cookies_from_set_cookie_headers,
    is_session_like_cookie,
    normalize_https_url,
    parse_set_cookie,
    redirect_targets_https,
)


def test_normalize_https_url_adds_scheme() -> None:
    assert normalize_https_url("example.com") == "https://example.com"
    assert normalize_https_url("https://example.com/path") == "https://example.com/path"


def test_parse_set_cookie_extracts_flags() -> None:
    cookie = parse_set_cookie("sessionid=abc; Path=/; Secure; HttpOnly; SameSite=Lax")
    assert cookie.name == "sessionid"
    assert cookie.secure is True
    assert cookie.httponly is True
    assert cookie.samesite == "Lax"


def test_cookies_from_set_cookie_headers() -> None:
    cookies = cookies_from_set_cookie_headers(
        {"Set-Cookie": "sid=1; HttpOnly", "Content-Type": "text/html"}
    )
    assert len(cookies) == 1
    assert cookies[0].name == "sid"


def test_is_session_like_cookie() -> None:
    assert is_session_like_cookie("sessionid") is True
    assert is_session_like_cookie("tracking_id") is False


def test_redirect_targets_https() -> None:
    assert redirect_targets_https("https://example.com/") is True
    assert redirect_targets_https("http://example.com/") is False
