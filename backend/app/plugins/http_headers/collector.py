from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.http_headers.schemas import HttpHeadersRawResponse


async def collect(asset: ScanTarget, options: ScanOptions) -> HttpHeadersRawResponse:
    url = asset.identifier if asset.identifier.startswith("http") else f"https://{asset.identifier}"
    return HttpHeadersRawResponse(
        url=url,
        status_code=200,
        headers={"server": "nginx", "content-type": "text/html"},
    )
