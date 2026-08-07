"""Collect raw HTTP responses — no findings."""

import time

import httpx

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.http_headers.schemas import (
    HttpHeadersRawResponse,
    HttpProbeRaw,
    HttpRedirect,
    HttpTiming,
    HttpTraceProbeRaw,
)
from app.plugins.http_headers.utils import (
    cookies_from_set_cookie_headers,
    normalize_https_url,
    to_http_url,
    truncate_body,
)
from app.plugins.shared.http_probe import fetch_path, fetch_primary

_API_SCHEMA_PATHS = (
    "/openapi.json",
    "/swagger.json",
    "/swagger/v1/swagger.json",
    "/v2/api-docs",
    "/v3/api-docs",
    "/api/swagger.json",
)


def _probe_from_cache(cached) -> HttpProbeRaw:
    return HttpProbeRaw(
        url=cached.url,
        final_url=cached.final_url,
        status_code=cached.status_code,
        headers=cached.headers,
        cookies=cookies_from_set_cookie_headers(cached.headers),
        redirects=[HttpRedirect(url=item.url, status_code=item.status_code) for item in cached.redirects],
        body=cached.body,
        body_length=cached.body_length,
        content_type=cached.content_type,
        timing=HttpTiming(total_ms=cached.timing_total_ms),
    )


async def _run_get_probe(
    client: httpx.AsyncClient,
    url: str,
    *,
    follow_redirects: bool = True,
) -> HttpProbeRaw:
    started_at = time.perf_counter()
    response = await client.get(url, follow_redirects=follow_redirects)
    from app.plugins.http_headers.utils import normalize_headers

    headers = normalize_headers(dict(response.headers))
    body_text = response.text
    body_preview, body_length = truncate_body(body_text)
    try:
        elapsed_ms = response.elapsed.total_seconds() * 1000
    except RuntimeError:
        elapsed_ms = None
    return HttpProbeRaw(
        url=url,
        final_url=str(response.url),
        status_code=response.status_code,
        headers=headers,
        cookies=cookies_from_set_cookie_headers(headers),
        redirects=[HttpRedirect(url=str(item.url), status_code=item.status_code) for item in response.history],
        body=body_preview,
        body_length=body_length,
        content_type=headers.get("content-type"),
        timing=HttpTiming(total_ms=(time.perf_counter() - started_at) * 1000, elapsed_ms=elapsed_ms),
    )


async def _run_trace_probe(client: httpx.AsyncClient, url: str) -> HttpTraceProbeRaw:
    try:
        response = await client.request("TRACE", url, follow_redirects=False)
    except httpx.HTTPError:
        return HttpTraceProbeRaw(url=url, status_code=None, allowed=False)

    preview, _ = truncate_body(response.text, limit=512)
    allowed = response.status_code not in {405, 501, 403} and response.status_code < 400

    return HttpTraceProbeRaw(
        url=url,
        status_code=response.status_code,
        allowed=allowed,
        response_preview=preview or None,
    )


async def _probe_api_schemas(identifier: str, timeout: float) -> list[str]:
    found: list[str] = []
    for path in _API_SCHEMA_PATHS:
        status_code, body = await fetch_path(identifier, path, timeout=min(timeout, 6.0))
        if status_code != 200 or not body:
            continue
        lowered = body.lower()
        if any(token in lowered for token in ("openapi", "swagger", '"paths"', "apiversion")):
            found.append(path)
    return found


async def collect(asset: ScanTarget, options: ScanOptions) -> HttpHeadersRawResponse:
    https_url = normalize_https_url(asset.identifier)
    timeout = httpx.Timeout(options.timeout, connect=min(options.timeout, 10.0))

    primary_cached = await fetch_primary(
        asset.identifier,
        timeout=options.timeout,
        user_agent="Sandbox-HTTP-Scanner/1.0 (+https://sandbox.local/scanner)",
    )
    primary = _probe_from_cache(primary_cached)

    headers = {
        "User-Agent": "Sandbox-HTTP-Scanner/1.0 (+https://sandbox.local/scanner)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True, verify=True) as client:
        http_probe = await _run_get_probe(client, to_http_url(https_url), follow_redirects=False)
        trace_probe = await _run_trace_probe(client, primary.final_url)

    api_schema_paths = await _probe_api_schemas(asset.identifier, options.timeout)

    return HttpHeadersRawResponse(
        primary=primary,
        http_probe=http_probe,
        trace_probe=trace_probe,
        api_schema_paths=api_schema_paths,
    )
