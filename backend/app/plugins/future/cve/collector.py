from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.future.cve.schemas import CveRawResponse, InstalledPackage


async def collect(asset: ScanTarget, options: ScanOptions) -> CveRawResponse:
    return CveRawResponse(
        host=asset.identifier,
        packages=[
            InstalledPackage(name="openssl", version="1.1.1", cve_ids=["CVE-2024-0001"], cvss=7.5),
        ],
    )
