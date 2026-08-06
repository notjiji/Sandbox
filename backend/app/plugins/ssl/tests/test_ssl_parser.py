import base64

from app.plugins.ssl.parser import parse
from app.plugins.ssl.schemas import CipherRaw, ProtocolProbeRaw, SslRawResponse
from app.plugins.ssl.tests.cert_factory import generate_self_signed_cert


def test_parse_builds_structured_ssl_data() -> None:
    der = generate_self_signed_cert(common_name="example.com", key_size=1024)
    raw = SslRawResponse(
        host="example.com",
        port=443,
        certificate_b64=base64.b64encode(der).decode("ascii"),
        negotiated_cipher=CipherRaw(name="ECDHE-RSA-AES128-GCM-SHA256", protocol="TLSv1.2", secret_bits=128),
        protocol_probes=[
            ProtocolProbeRaw(version="TLSv1.2", accepted=True, negotiated="TLSv1.2"),
            ProtocolProbeRaw(version="TLSv1.0", accepted=True, negotiated="TLSv1.0"),
        ],
    )

    parsed = parse(raw)

    assert parsed.host == "example.com"
    assert "TLSv1.2" in parsed.protocols_accepted
    assert parsed.certificate.public_key_bits == 1024
    assert parsed.cipher is not None
    assert parsed.cipher.forward_secrecy is True
    assert parsed.cipher.key_exchange == "ECDHE"
