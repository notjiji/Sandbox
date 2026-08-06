"""Collect raw TLS/certificate data — no findings."""

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.ssl.schemas import SslRawResponse


async def collect(asset: ScanTarget, options: ScanOptions) -> SslRawResponse:
    host = asset.identifier.replace("https://", "").replace("http://", "").split("/")[0]
    return SslRawResponse(
        host=host,
        port=443,
        tls_versions_detected=["TLSv1.0", "TLSv1.2", "TLSv1.3"],
        certificate={
            "issuer": "Let's Encrypt",
            "not_after": "2026-12-01T00:00:00Z",
            "cipher_suites": ["ECDHE-RSA-AES128-GCM-SHA256", "ECDHE-RSA-AES128-SHA"],
        },
    )
