from app.plugins.ssl.parser import parse
from app.plugins.ssl.schemas import SslRawResponse


def test_parse_extracts_protocols_and_certificate_fields() -> None:
    raw = SslRawResponse(
        host="example.com",
        port=443,
        tls_versions_detected=["TLSv1.2", "TLSv1.3"],
        certificate={"issuer": "Let's Encrypt", "not_after": "2026-12-01", "cipher_suites": ["AES128"]},
    )

    parsed = parse(raw)

    assert parsed.protocols == ["TLSv1.2", "TLSv1.3"]
    assert parsed.issuer == "Let's Encrypt"
    assert parsed.expires == "2026-12-01"
    assert parsed.cipher_suites == ["AES128"]
