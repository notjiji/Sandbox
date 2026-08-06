from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.tls.schemas import TlsRawResponse


async def collect(asset: ScanTarget, options: ScanOptions) -> TlsRawResponse:
    host = asset.identifier.replace("https://", "").replace("http://", "").split("/")[0]
    return TlsRawResponse(
        host=host,
        negotiated_cipher="ECDHE-RSA-AES128-SHA",
        min_version="TLSv1.2",
        cipher_count=12,
    )
