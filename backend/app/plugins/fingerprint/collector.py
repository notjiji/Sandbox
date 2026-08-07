"""Collect HTTP headers, HTML, scripts, and cookies for fingerprinting."""

import time

import httpx
from bs4 import BeautifulSoup

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.fingerprint.schemas import FingerprintCookieRaw, FingerprintRawResponse
from app.plugins.http_headers.utils import (
    cookies_from_set_cookie_headers,
    normalize_headers,
    normalize_https_url,
    truncate_body,
)


def _extract_script_srcs(body: str, *, limit: int = 50) -> list[str]:
    if not body:
        return []
    soup = BeautifulSoup(body, "html.parser")
    srcs: list[str] = []
    for tag in soup.find_all("script"):
        src = tag.get("src")
        if isinstance(src, str) and src.strip():
            srcs.append(src.strip())
        if len(srcs) >= limit:
            break
    return srcs


async def collect(asset: ScanTarget, options: ScanOptions) -> FingerprintRawResponse:
    https_url = normalize_https_url(asset.identifier)
    timeout = httpx.Timeout(options.timeout, connect=min(options.timeout, 10.0))
    headers = {
        "User-Agent": "Sandbox-Fingerprint-Scanner/1.0 (+https://sandbox.local/scanner)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    started_at = time.perf_counter()
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            headers=headers,
            follow_redirects=True,
            verify=True,
        ) as client:
            response = await client.get(https_url, follow_redirects=True)
    except httpx.HTTPError as exc:
        return FingerprintRawResponse(
            url=https_url,
            final_url=https_url,
            error=str(exc),
        )

    _ = (time.perf_counter() - started_at) * 1000
    normalized = normalize_headers(dict(response.headers))
    body_text = response.text
    body_preview, body_length = truncate_body(body_text, limit=16384)
    script_srcs = _extract_script_srcs(body_preview)
    cookies = [
        FingerprintCookieRaw(name=cookie.name, value=cookie.value)
        for cookie in cookies_from_set_cookie_headers(normalized)
    ]

    return FingerprintRawResponse(
        url=https_url,
        final_url=str(response.url),
        status_code=response.status_code,
        headers=normalized,
        cookies=cookies,
        body=body_preview,
        body_length=body_length,
        script_srcs=script_srcs,
    )
