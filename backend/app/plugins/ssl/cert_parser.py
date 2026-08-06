"""X.509 certificate parsing via cryptography."""

from __future__ import annotations

import base64
from datetime import UTC, datetime

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dsa, ec, rsa
from cryptography.x509.oid import ExtensionOID, NameOID

from app.plugins.ssl.schemas import ParsedCertificate
from app.plugins.ssl.utils import hostname_matches_pattern


def _name_attr_values(name: x509.Name, oid: NameOID) -> list[str]:
    return [attr.value for attr in name if attr.oid == oid]


def _extract_sans(cert: x509.Certificate) -> list[str]:
    try:
        ext = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
    except x509.ExtensionNotFound:
        return []
    return [entry.value for entry in ext.value if isinstance(entry.value, str)]


def _public_key_info(cert: x509.Certificate) -> tuple[str | None, int | None]:
    public_key = cert.public_key()
    if isinstance(public_key, rsa.RSAPublicKey):
        return "RSA", public_key.key_size
    if isinstance(public_key, ec.EllipticCurvePublicKey):
        return "EC", public_key.key_size
    if isinstance(public_key, dsa.DSAPublicKey):
        return "DSA", public_key.key_size
    return public_key.__class__.__name__, getattr(public_key, "key_size", None)


def _signature_algorithm(cert: x509.Certificate) -> str | None:
    if cert.signature_hash_algorithm is None:
        return cert.signature_algorithm_oid._name_
    return cert.signature_hash_algorithm.name


def parse_certificate_der(der_bytes: bytes, *, hostname: str) -> ParsedCertificate:
    cert = x509.load_der_x509_certificate(der_bytes, default_backend())
    issuer = cert.issuer.rfc4514_string()
    subject = cert.subject.rfc4514_string()
    common_name = (_name_attr_values(cert.subject, NameOID.COMMON_NAME) or [None])[0]
    sans = _extract_sans(cert)
    not_before = cert.not_valid_before_utc
    not_after = cert.not_valid_after_utc
    now = datetime.now(UTC)
    days_until_expiry = (not_after - now).days
    key_algorithm, key_bits = _public_key_info(cert)

    wildcard = False
    if common_name and common_name.startswith("*."):
        wildcard = True
    if any(san.startswith("*.") for san in sans):
        wildcard = True

    return ParsedCertificate(
        issuer=issuer,
        subject=subject,
        common_name=common_name,
        sans=sans,
        not_before=not_before,
        not_after=not_after,
        is_expired=not_after < now,
        days_until_expiry=days_until_expiry,
        is_wildcard=wildcard,
        is_self_signed=issuer == subject,
        signature_algorithm=_signature_algorithm(cert),
        public_key_algorithm=key_algorithm,
        public_key_bits=key_bits,
    )


def hostname_matches_certificate(hostname: str, certificate: ParsedCertificate) -> bool:
    candidates = []
    if certificate.common_name:
        candidates.append(certificate.common_name)
    candidates.extend(certificate.sans)
    return any(hostname_matches_pattern(hostname, candidate) for candidate in candidates)


def analyze_san_coverage(host: str, certificate: ParsedCertificate) -> tuple[bool, bool]:
    host = host.lower().split(":")[0]
    if host.startswith("www."):
        apex, www = host[4:], host
    else:
        apex, www = host, f"www.{host}"
    return (
        hostname_matches_certificate(apex, certificate),
        hostname_matches_certificate(www, certificate),
    )


def parse_certificate_b64(certificate_b64: str | None, *, hostname: str) -> ParsedCertificate:
    if not certificate_b64:
        return ParsedCertificate(issuer="unknown", subject="unknown")
    return parse_certificate_der(base64.b64decode(certificate_b64), hostname=hostname)
