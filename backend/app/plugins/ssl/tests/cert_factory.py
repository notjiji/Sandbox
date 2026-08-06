"""Generate test certificates."""

from datetime import UTC, datetime, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def generate_self_signed_cert(
    *,
    common_name: str = "example.com",
    days_valid: int = 90,
    key_size: int = 2048,
    san_names: list[str] | None = None,
    signature_hash=hashes.SHA256(),
    expired: bool = False,
) -> bytes:
    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])

    now = datetime.now(UTC)
    if expired:
        not_before = now - timedelta(days=400)
        not_after = now - timedelta(days=1)
    else:
        not_before = now - timedelta(days=1)
        not_after = now + timedelta(days=days_valid)

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before)
        .not_valid_after(not_after)
    )

    names = san_names or [common_name]
    builder = builder.add_extension(
        x509.SubjectAlternativeName([x509.DNSName(name) for name in names]),
        critical=False,
    )

    cert = builder.sign(key, signature_hash)
    return cert.public_bytes(serialization.Encoding.DER)
