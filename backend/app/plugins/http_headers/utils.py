"""Shared helpers for the HTTP scanner."""

from urllib.parse import urlparse

from app.plugins.http_headers.schemas import HttpCookieRaw

_BODY_PREVIEW_LIMIT = 8192
_SESSION_COOKIE_NAMES = frozenset(
    {"session", "sessionid", "sess", "auth", "token", "jwt", "sid", "connect.sid"}
)


def normalize_https_url(identifier: str) -> str:
    cleaned = identifier.strip()
    if cleaned.startswith(("http://", "https://")):
        parsed = urlparse(cleaned)
        if not parsed.netloc:
            raise ValueError(f"Invalid URL identifier: {identifier}")
        return cleaned if cleaned.startswith("https://") else cleaned.replace("http://", "https://", 1)
    host = cleaned.split("/")[0]
    path = cleaned[len(host) :] or ""
    return f"https://{host}{path}"


def to_http_url(https_url: str) -> str:
    if https_url.startswith("https://"):
        return "http://" + https_url[len("https://") :]
    if https_url.startswith("http://"):
        return https_url
    return f"http://{https_url}"


def header_lookup(headers: dict[str, str], name: str) -> str | None:
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return None


def normalize_headers(headers: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in headers.items()}


def truncate_body(body: str, limit: int = _BODY_PREVIEW_LIMIT) -> tuple[str, int]:
    length = len(body)
    if length <= limit:
        return body, length
    return body[:limit], length


def parse_set_cookie(header: str) -> HttpCookieRaw:
    parts = [part.strip() for part in header.split(";")]
    name_value = parts[0]
    if "=" in name_value:
        name, value = name_value.split("=", 1)
    else:
        name, value = name_value, ""

    attrs: dict[str, str | None] = {}
    flags: set[str] = set()
    for part in parts[1:]:
        if "=" in part:
            key, val = part.split("=", 1)
            attrs[key.lower()] = val.strip()
        else:
            flags.add(part.lower())

    samesite = attrs.get("samesite")
    max_age_raw = attrs.get("max-age")
    max_age = int(max_age_raw) if max_age_raw and max_age_raw.isdigit() else None

    return HttpCookieRaw(
        name=name.strip(),
        value=value.strip(),
        domain=attrs.get("domain"),
        path=attrs.get("path"),
        secure="secure" in flags,
        httponly="httponly" in flags,
        samesite=samesite,
        expires=attrs.get("expires"),
        max_age=max_age,
        raw=header,
    )


def cookies_from_set_cookie_headers(headers: dict[str, str]) -> list[HttpCookieRaw]:
    cookies: list[HttpCookieRaw] = []
    for key, value in headers.items():
        if key.lower() == "set-cookie":
            cookies.append(parse_set_cookie(value))
    return cookies


def is_session_like_cookie(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in _SESSION_COOKIE_NAMES)


def redirect_targets_https(location: str | None) -> bool:
    if not location:
        return False
    return location.lower().startswith("https://")
