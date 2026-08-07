import asyncio

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.future.cve.osv import hints_from_http_headers, hints_from_services, query_osv
from app.plugins.future.cve.schemas import CveRawResponse, InstalledPackage
from app.plugins.shared.http_probe import fetch_primary
from app.plugins.shared.scan_context import scan_context


async def collect(asset: ScanTarget, options: ScanOptions) -> CveRawResponse:
    host = asset.identifier.replace("https://", "").replace("http://", "").split("/")[0]
    timeout = min(options.timeout, 15.0)

    hints = []
    try:
        probe = await fetch_primary(
            asset.identifier,
            timeout=timeout,
            user_agent="Sandbox-CVE-Scanner/1.0 (+https://sandbox.local/scanner)",
        )
        hints.extend(hints_from_http_headers(probe.headers))
    except (ValueError, OSError):
        pass

    hints.extend(hints_from_services(scan_context.service_hints()))

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
