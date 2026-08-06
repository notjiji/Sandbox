from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.dns.schemas import DnsRawResponse


async def collect(asset: ScanTarget, options: ScanOptions) -> DnsRawResponse:
    domain = asset.identifier.replace("https://", "").replace("http://", "").split("/")[0]
    return DnsRawResponse(
        domain=domain,
        records={"A": ["203.0.113.10"]},
    )
