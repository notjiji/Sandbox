import base64

from app.plugins.ssl.cert_parser import hostname_matches_certificate, parse_certificate_der
from app.plugins.ssl.tests.cert_factory import generate_self_signed_cert


def test_parse_certificate_extracts_sans_and_key_info() -> None:
    der = generate_self_signed_cert(common_name="example.com", san_names=["example.com", "*.example.com"])
    parsed = parse_certificate_der(der, hostname="example.com")

    assert parsed.common_name == "example.com"
    assert "example.com" in parsed.sans
    assert parsed.public_key_algorithm == "RSA"
    assert parsed.public_key_bits == 2048
    assert parsed.is_self_signed is True
    assert parsed.is_wildcard is True


def test_parse_certificate_detects_expired() -> None:
    der = generate_self_signed_cert(expired=True)
    parsed = parse_certificate_der(der, hostname="example.com")
    assert parsed.is_expired is True


def test_hostname_matches_certificate() -> None:
    der = generate_self_signed_cert(common_name="*.example.com", san_names=["*.example.com"])
    parsed = parse_certificate_der(der, hostname="example.com")
    assert hostname_matches_certificate("www.example.com", parsed) is True
    assert hostname_matches_certificate("other.com", parsed) is False
