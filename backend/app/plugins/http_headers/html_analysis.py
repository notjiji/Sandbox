"""HTML/CSS mixed-content detection."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

_URL_ATTRS = ("src", "href", "data", "poster")
_HTTP_URL_RE = re.compile(r"""url\(\s*['"]?(http://[^)'"]+)""", re.IGNORECASE)
_INLINE_HTTP_RE = re.compile(r"""http://[^\s"'<>]+""", re.IGNORECASE)


def _is_http_url(url: str) -> bool:
    return url.lower().startswith("http://")


def _normalize_candidate(url: str, base_url: str) -> str | None:
    cleaned = url.strip().strip("'\"")
    if not cleaned or cleaned.startswith(("data:", "blob:", "javascript:", "mailto:", "#")):
        return None
    absolute = urljoin(base_url, cleaned)
    parsed = urlparse(absolute)
    if parsed.scheme == "http":
        return absolute
    return None


def find_mixed_content_html(body: str, *, page_url: str, is_https: bool, limit: int = 15) -> list[str]:
    if not is_https or not body:
        return []

    found: list[str] = []
    seen: set[str] = set()

    def add(url: str | None) -> None:
        if url and url not in seen:
            seen.add(url)
            found.append(url)

    soup = BeautifulSoup(body, "html.parser")
    for tag in soup.find_all(True):
        for attr in _URL_ATTRS:
            value = tag.get(attr)
            if isinstance(value, str):
                add(_normalize_candidate(value, page_url))
        style = tag.get("style")
        if isinstance(style, str):
            for match in _HTTP_URL_RE.findall(style):
                add(_normalize_candidate(match, page_url))

    for style_tag in soup.find_all("style"):
        text = style_tag.string or style_tag.get_text()
        if text:
            for match in _HTTP_URL_RE.findall(text):
                add(_normalize_candidate(match, page_url))

    if len(found) < limit:
        for match in _INLINE_HTTP_RE.findall(body):
            add(_normalize_candidate(match, page_url))
            if len(found) >= limit:
                break

    return found[:limit]
