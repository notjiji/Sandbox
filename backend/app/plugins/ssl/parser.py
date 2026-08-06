"""Convert raw TLS responses into structured objects."""

from app.plugins.ssl.schemas import SslParsedData, SslRawResponse


def parse(raw: SslRawResponse) -> SslParsedData:
    cert = raw.certificate
    return SslParsedData(
        protocols=raw.tls_versions_detected,
        issuer=cert.get("issuer", "unknown"),
        expires=cert.get("not_after", ""),
        cipher_suites=cert.get("cipher_suites", []),
    )
