"""Collect Set-Cookie headers from the target."""

from urllib.parse import urlparse

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.cookies.schemas import CookiesRawResponse
from app.plugins.shared.http_probe import fetch_primary


async def collect(asset: ScanTarget, options: ScanOptions) -> CookiesRawResponse:
    probe = await fetch_primary(
        asset.identifier,
        timeout=options.timeout,
        user_agent="Sandbox-Cookie-Scanner/2.0 (+https://sandbox.local/scanner)",
    )
    is_https = urlparse(probe.final_url).scheme == "https"
    return CookiesRawResponse(
        url=probe.url,
        final_url=probe.final_url,
        is_https=is_https,
        set_cookie_headers=list(probe.set_cookie_headers),
    )
