from datetime import UTC, datetime, timedelta

from app.plugins.base.plugin import ScanTarget
from app.plugins.ssl.rules import (
    evaluate_rules,
    rule_expired_certificate,
    rule_hostname_mismatch,
    rule_self_signed,
    rule_tls10_enabled,
    rule_tls11_enabled,
    rule_weak_rsa_key,
)
from app.plugins.ssl.schemas import ParsedCertificate, ParsedCipher, SslParsedData

ASSET = ScanTarget(asset_id="1", identifier="example.com", asset_type="website")


def _parsed(**kwargs) -> SslParsedData:
    cert_defaults = {
        "issuer": "CN=Test CA",
        "subject": "CN=example.com",
        "common_name": "example.com",
        "sans": ["example.com"],
        "not_after": datetime.now(UTC) + timedelta(days=120),
        "days_until_expiry": 120,
        "is_expired": False,
        "public_key_algorithm": "RSA",
        "public_key_bits": 2048,
        "signature_algorithm": "sha256",
    }
    cert_defaults.update(kwargs.pop("certificate", {}))
    defaults = {
        "host": "example.com",
        "port": 443,
        "protocols": ["TLSv1.2"],
        "protocols_accepted": ["TLSv1.2"],
        "certificate": ParsedCertificate(**cert_defaults),
        "cipher": ParsedCipher(name="ECDHE-RSA-AES128-GCM-SHA256", protocol="TLSv1.2", secret_bits=128),
        "hostname_matches": True,
        "chain_trusted": True,
        "ocsp_stapling": True,
        "weak_ciphers_accepted": [],
        "san_covers_apex": True,
        "san_covers_www": True,
        "cipher_is_weak": False,
        "lacks_forward_secrecy": False,
    }
    defaults.update(kwargs)
    return SslParsedData(**defaults)


def test_rule_tls10_enabled() -> None:
    finding = rule_tls10_enabled(_parsed(protocols_accepted=["TLSv1.0", "TLSv1.2"]), ASSET, "ssl")
    assert finding is not None
    assert finding.rule_id == "SSL_TLS10_ENABLED"


def test_rule_tls11_enabled() -> None:
    finding = rule_tls11_enabled(_parsed(protocols_accepted=["TLSv1.1"]), ASSET, "ssl")
    assert finding is not None
    assert finding.rule_id == "SSL_TLS11_ENABLED"


def test_rule_expired_certificate() -> None:
    cert = ParsedCertificate(
        issuer="CN=x",
        subject="CN=x",
        is_expired=True,
        not_after=datetime.now(UTC) - timedelta(days=1),
    )
    finding = rule_expired_certificate(_parsed(certificate=cert.model_dump()), ASSET, "ssl")
    assert finding is not None
    assert finding.rule_id == "SSL_EXPIRED"


def test_rule_weak_rsa_key() -> None:
    cert = ParsedCertificate(
        issuer="CN=CA",
        subject="CN=example.com",
        public_key_algorithm="RSA",
        public_key_bits=1024,
    )
    finding = rule_weak_rsa_key(_parsed(certificate=cert.model_dump()), ASSET, "ssl")
    assert finding is not None
    assert finding.rule_id == "SSL_WEAK_RSA_KEY"


def test_rule_self_signed() -> None:
    cert = ParsedCertificate(issuer="CN=example.com", subject="CN=example.com", is_self_signed=True)
    finding = rule_self_signed(_parsed(certificate=cert.model_dump()), ASSET, "ssl")
    assert finding is not None
    assert finding.rule_id == "SSL_SELF_SIGNED"


def test_rule_hostname_mismatch() -> None:
    finding = rule_hostname_mismatch(_parsed(hostname_matches=False), ASSET, "ssl")
    assert finding is not None
    assert finding.rule_id == "SSL_HOSTNAME_MISMATCH"


def test_evaluate_rules_tls10_only() -> None:
    findings = evaluate_rules(_parsed(protocols_accepted=["TLSv1.0"]), ASSET, plugin_id="ssl")
    rule_ids = {finding.rule_id for finding in findings}
    assert "SSL_TLS10_ENABLED" in rule_ids


def test_evaluate_rules_passes_for_secure_config() -> None:
    findings = evaluate_rules(_parsed(), ASSET, plugin_id="ssl")
    assert findings == []
