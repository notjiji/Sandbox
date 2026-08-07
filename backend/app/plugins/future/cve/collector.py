import asyncio

import httpx

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.future.cve.osv import hints_from_http_headers, hints_from_ssh_banner, query_osv
from app.plugins.future.cve.schemas import CveRawResponse, InstalledPackage
from app.plugins.ports.scanner import probe_port, resolve_host


async def _http_headers(host: str, timeout: float) -> dict[str, str]:
    for scheme in ("https", "http"):
        url = f"{scheme}://{host}/"
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, verify=False) as client:
                response = await client.get(url)
                return {key.lower(): value for key, value in response.headers.items()}
        except httpx.HTTPError:
            continue
    return {}


async def collect(asset: ScanTarget, options: ScanOptions) -> CveRawResponse:
    host = resolve_host(asset.identifier)
    timeout = min(options.timeout, 15.0)

    headers, ssh_probe = await asyncio.gather(
        _http_headers(host, timeout),
        probe_port(host, 22, min(timeout, 3.0)),
    )

    hints = hints_from_http_headers(headers)
    hints.extend(hints_from_ssh_banner(ssh_probe.banner))

    packages: list[InstalledPackage] = []
    seen: set[tuple[str, str]] = set()
    for hint in hints:
        key = (hint.product, hint.version)
        if key in seen:
            continue
        seen.add(key)
        vulns = await asyncio.to_thread(query_osv, hint.product, hint.version, hint.ecosystem)
        cve_ids = [item["cve_id"] for item in vulns if item.get("cve_id")]
        top_cvss = next((item["cvss"] for item in vulns if item.get("cvss") is not None), None)
        packages.append(
            InstalledPackage(
                name=hint.product,
                version=hint.version,
                cve_ids=cve_ids,
                cvss=top_cvss,
                source=hint.source,
            )
        )

    return CveRawResponse(host=host, packages=packages)
