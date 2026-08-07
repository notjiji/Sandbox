"""Download /.well-known/security.txt."""

import httpx

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.http_headers.utils import normalize_https_url, security_txt_url
from app.plugins.security_txt.schemas import SecurityTxtRawResponse


async def collect(asset: ScanTarget, options: ScanOptions) -> SecurityTxtRawResponse:
    base_url = normalize_https_url(asset.identifier)
    url = security_txt_url(base_url)
    timeout = httpx.Timeout(options.timeout, connect=min(options.timeout, 10.0))
    headers = {
        "User-Agent": "Sandbox-SecurityTxt-Scanner/1.0 (+https://sandbox.local/scanner)",
        "Accept": "text/plain,*/*",
    }

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            headers=headers,
            follow_redirects=True,
            verify=True,
        ) as client:
            response = await client.get(url, follow_redirects=True)
    except httpx.HTTPError as exc:
        return SecurityTxtRawResponse(url=url, error=str(exc))

    body = response.text if response.status_code == 200 else ""
    return SecurityTxtRawResponse(
        url=url,
        final_url=str(response.url),
        body=body,
        status_code=response.status_code,
    )
