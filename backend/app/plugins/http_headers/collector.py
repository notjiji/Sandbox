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
    normalize_headers,
    normalize_https_url,
    security_txt_url,
    to_http_url,
    truncate_body,
)


def _build_probe_result(
    *,
    request_url: str,
    response: httpx.Response,
    started_at: float,
) -> HttpProbeRaw:
    total_ms = (time.perf_counter() - started_at) * 1000
    headers = normalize_headers(dict(response.headers))
    body_text = response.text
    try:
        elapsed_ms = response.elapsed.total_seconds() * 1000
    except RuntimeError:
        elapsed_ms = None
    body_preview, body_length = truncate_body(body_text)
    redirects = [
        HttpRedirect(url=str(item.url), status_code=item.status_code) for item in response.history
    ]

    return HttpProbeRaw(
        url=request_url,
        final_url=str(response.url),
        status_code=response.status_code,
        headers=headers,
        cookies=cookies_from_set_cookie_headers(headers),
        redirects=redirects,
        body=body_preview,
        body_length=body_length,
        content_type=headers.get("content-type"),
        timing=HttpTiming(total_ms=total_ms, elapsed_ms=elapsed_ms),
    )


async def _run_get_probe(
    client: httpx.AsyncClient,
    url: str,
    *,
    follow_redirects: bool = True,
) -> HttpProbeRaw:
    started_at = time.perf_counter()
    response = await client.get(url, follow_redirects=follow_redirects)
    return _build_probe_result(request_url=url, response=response, started_at=started_at)


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


async def collect(asset: ScanTarget, options: ScanOptions) -> HttpHeadersRawResponse:
    https_url = normalize_https_url(asset.identifier)
    timeout = httpx.Timeout(options.timeout, connect=min(options.timeout, 10.0))

    headers = {
        "User-Agent": "Sandbox-HTTP-Scanner/1.0 (+https://sandbox.local/scanner)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    async with httpx.AsyncClient(
        timeout=timeout,
        headers=headers,
        follow_redirects=True,
        verify=True,
    ) as client:
        primary = await _run_get_probe(client, https_url, follow_redirects=True)
        http_probe = await _run_get_probe(client, to_http_url(https_url), follow_redirects=False)
        trace_probe = await _run_trace_probe(client, primary.final_url)
        try:
            security_txt_probe = await _run_get_probe(
                client, security_txt_url(primary.final_url), follow_redirects=True
            )
        except httpx.HTTPError:
            security_txt_probe = None

    return HttpHeadersRawResponse(
        primary=primary,
        http_probe=http_probe,
        trace_probe=trace_probe,
        security_txt_probe=security_txt_probe,
    )
