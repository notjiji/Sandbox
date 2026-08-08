"""Parse Set-Cookie headers into structured cookie models."""

from __future__ import annotations

from app.plugins.cookies.schemas import CookieRaw, CookiesParsedData, CookiesRawResponse
from app.plugins.http_headers.utils import is_session_like_cookie, parse_set_cookie

_SENSITIVE_TOKENS = frozenset({"session", "jwt", "token", "auth", "sess", "sid", "access", "refresh", "id"})
_WEAK_NAMES = frozenset({"user", "admin", "password", "token"})
_TOO_MANY_COOKIES = 20
_MAX_COOKIE_SIZE = 4096
_LONG_MAX_AGE_SECONDS = 365 * 24 * 60 * 60


def _is_sensitive(name: str) -> bool:
    lowered = name.lower()
    return is_session_like_cookie(name) or any(token in lowered for token in _SENSITIVE_TOKENS)


def _is_weak_name(name: str) -> bool:
    return name.lower() in _WEAK_NAMES


def _is_persistent(cookie: CookieRaw) -> bool:
    return bool(cookie.expires or (cookie.max_age is not None and cookie.max_age > 0))


def _has_long_expiration(cookie: CookieRaw) -> bool:
    if cookie.max_age is not None and cookie.max_age > _LONG_MAX_AGE_SECONDS:
        return True
    return _is_persistent(cookie) and cookie.max_age is None and bool(cookie.expires)


def _to_cookie_raw(header: str) -> CookieRaw:
    parsed = parse_set_cookie(header)
    size_bytes = len(header.encode("utf-8", errors="replace"))
    cookie = CookieRaw(
        name=parsed.name,
        value=parsed.value,
        secure=parsed.secure,
        httponly=parsed.httponly,
        samesite=parsed.samesite,
        expires=parsed.expires,
        max_age=parsed.max_age,
        domain=parsed.domain,
        path=parsed.path,
        size_bytes=size_bytes,
        raw=header,
    )
    cookie.is_sensitive = _is_sensitive(cookie.name)
    cookie.weak_name = _is_weak_name(cookie.name)
    cookie.is_persistent = _is_persistent(cookie)
    return cookie


def parse(raw: CookiesRawResponse) -> CookiesParsedData:
    cookies = [_to_cookie_raw(header) for header in raw.set_cookie_headers]

    name_counts: dict[str, int] = {}
    for cookie in cookies:
        name_counts[cookie.name] = name_counts.get(cookie.name, 0) + 1

    duplicate_names = sorted(name for name, count in name_counts.items() if count > 1)
    sensitive_cookies = [cookie for cookie in cookies if cookie.is_sensitive]
    weak_name_cookies = [cookie.name for cookie in cookies if cookie.weak_name]

    missing_secure = [
        cookie
        for cookie in cookies
        if raw.is_https and not cookie.secure
    ]
    missing_httponly = [cookie for cookie in cookies if not cookie.httponly]
    missing_samesite = [cookie for cookie in cookies if not cookie.samesite]
    long_expiration = [cookie for cookie in cookies if _has_long_expiration(cookie)]
    oversized = [cookie for cookie in cookies if cookie.size_bytes > _MAX_COOKIE_SIZE]

    return CookiesParsedData(
        url=raw.url,
        final_url=raw.final_url,
        is_https=raw.is_https,
        cookies=cookies,
        sensitive_cookies=sensitive_cookies,
        duplicate_names=duplicate_names,
        weak_name_cookies=weak_name_cookies,
        cookie_count=len(cookies),
        has_too_many_cookies=len(cookies) > _TOO_MANY_COOKIES,
        cookies_missing_secure=missing_secure,
        cookies_missing_httponly=missing_httponly,
        cookies_missing_samesite=missing_samesite,
        cookies_long_expiration=long_expiration,
        cookies_oversized=oversized,
    )
