"""Cookie scanner data models."""

from app.shared.schemas.base import BaseSchema


class CookieRaw(BaseSchema):
    name: str
    value: str = ""
    secure: bool = False
    httponly: bool = False
    samesite: str | None = None
    expires: str | None = None
    max_age: int | None = None
    domain: str | None = None
    path: str | None = None
    size_bytes: int = 0
    is_sensitive: bool = False
    is_persistent: bool = False
    weak_name: bool = False
    raw: str | None = None


class CookiesRawResponse(BaseSchema):
    url: str
    final_url: str
    is_https: bool
    set_cookie_headers: list[str] = []


class CookiesParsedData(BaseSchema):
    url: str
    final_url: str
    is_https: bool
    cookies: list[CookieRaw] = []
    sensitive_cookies: list[CookieRaw] = []
    duplicate_names: list[str] = []
    weak_name_cookies: list[str] = []
    cookie_count: int = 0
    has_too_many_cookies: bool = False
    cookies_missing_secure: list[CookieRaw] = []
    cookies_missing_httponly: list[CookieRaw] = []
    cookies_missing_samesite: list[CookieRaw] = []
    cookies_long_expiration: list[CookieRaw] = []
    cookies_oversized: list[CookieRaw] = []
