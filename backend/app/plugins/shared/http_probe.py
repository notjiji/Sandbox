"""Shared HTTP primary probe with per-scan deduplication."""

from __future__ import annotations

import time

import httpx

from app.plugins.http_headers.utils import (
    cookies_from_set_cookie_headers,
    header_lookup,
    normalize_headers,
    normalize_https_url,
    truncate_body,
)
from app.plugins.shared.scan_context import CachedHttpProbe, CachedHttpRedirect, scan_context


async def fetch_primary(
    identifier: str,
    *,
    timeout: float,
    user_agent: str = "Sandbox-HTTP-Probe/1.0 (+https://sandbox.local/scanner)",
) -> CachedHttpProbe:
    url = normalize_https_url(identifier)
    cache_key = url.lower()

    cached = scan_context.get_http_primary(cache_key)
    if cached is not None:
        return cached

    lock = scan_context.lock_for(cache_key)
    async with lock:
        cached = scan_context.get_http_primary(cache_key)
        if cached is not None:
            return cached

        timeout_cfg = httpx.Timeout(timeout, connect=min(timeout, 10.0))
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        started_at = time.perf_counter()
        async with httpx.AsyncClient(timeout=timeout_cfg, headers=headers, follow_redirects=True, verify=True) as client:
            response = await client.get(url, follow_redirects=True)

        body_text = response.text
        body_preview, body_length = truncate_body(body_text)
        normalized = normalize_headers(dict(response.headers))
        set_cookie_headers = (
            list(response.headers.get_list("set-cookie"))
            if hasattr(response.headers, "get_list")
            else [value for key, value in response.headers.items() if key.lower() == "set-cookie"]
        )
        probe = CachedHttpProbe(
            url=url,
            final_url=str(response.url),
            status_code=response.status_code,
            headers=normalized,
            body=body_preview,
            body_length=body_length,
            cookies=[
                {"name": cookie.name, "value": cookie.value}
                for cookie in cookies_from_set_cookie_headers(normalized)
            ],
            set_cookie_headers=set_cookie_headers,
            redirects=[
                CachedHttpRedirect(url=str(item.url), status_code=item.status_code) for item in response.history
            ],
            content_type=header_lookup(normalized, "content-type"),
            timing_total_ms=(time.perf_counter() - started_at) * 1000,
        )
        scan_context.set_http_primary(cache_key, probe)
        return probe


async def fetch_path(
    base_identifier: str,
    path: str,
    *,
    timeout: float,
) -> tuple[int | None, str]:
    base = normalize_https_url(base_identifier).rstrip("/")
    url = f"{base}{path if path.startswith('/') else '/' + path}"
    timeout_cfg = httpx.Timeout(min(timeout, 8.0), connect=min(timeout, 5.0))
    try:
        async with httpx.AsyncClient(timeout=timeout_cfg, follow_redirects=True, verify=True) as client:
            response = await client.get(url)
            preview, _ = truncate_body(response.text, limit=2048)
            return response.status_code, preview
    except httpx.HTTPError:
        return None, ""
