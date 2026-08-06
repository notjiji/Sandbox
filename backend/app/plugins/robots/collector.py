from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.robots.schemas import RobotsRawResponse


async def collect(asset: ScanTarget, options: ScanOptions) -> RobotsRawResponse:
    base = asset.identifier if asset.identifier.startswith("http") else f"https://{asset.identifier}"
    return RobotsRawResponse(
        url=f"{base.rstrip('/')}/robots.txt",
        status_code=200,
        body="User-agent: *\nDisallow: /private\nDisallow: /tmp\nAllow: /",
    )
