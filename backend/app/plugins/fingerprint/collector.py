"""Collect HTTP headers, HTML, scripts, and cookies for fingerprinting."""

from bs4 import BeautifulSoup

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.fingerprint.schemas import FingerprintCookieRaw, FingerprintRawResponse
from app.plugins.shared.http_probe import fetch_primary


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
    try:
        probe = await fetch_primary(
            asset.identifier,
            timeout=options.timeout,
            user_agent="Sandbox-Fingerprint-Scanner/1.0 (+https://sandbox.local/scanner)",
        )
    except ValueError as exc:
        return FingerprintRawResponse(url=asset.identifier, final_url=asset.identifier, error=str(exc))
    except Exception as exc:
        return FingerprintRawResponse(url=asset.identifier, final_url=asset.identifier, error=str(exc))

    body_preview = probe.body
    script_srcs = _extract_script_srcs(body_preview)
    cookies = [FingerprintCookieRaw(name=item["name"], value=item["value"]) for item in probe.cookies]

    return FingerprintRawResponse(
        url=probe.url,
        final_url=probe.final_url,
        status_code=probe.status_code,
        headers=probe.headers,
        cookies=cookies,
        body=body_preview,
        body_length=probe.body_length,
        script_srcs=script_srcs,
    )
