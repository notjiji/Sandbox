from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.whois.schemas import WhoisRawResponse


async def collect(asset: ScanTarget, options: ScanOptions) -> WhoisRawResponse:
    domain = asset.identifier.replace("https://", "").replace("http://", "").split("/")[0]
    return WhoisRawResponse(domain=domain, expires="2026-08-24", days_until_expiry=21)
