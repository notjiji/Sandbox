from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.cookies.schemas import CookiesRawResponse


async def collect(asset: ScanTarget, options: ScanOptions) -> CookiesRawResponse:
    url = asset.identifier if asset.identifier.startswith("http") else f"https://{asset.identifier}"
    return CookiesRawResponse(
        url=url,
        set_cookie_headers=[
            "sessionid=abc123; Path=/",
            "tracking=xyz; Path=/; Secure; HttpOnly",
        ],
    )
