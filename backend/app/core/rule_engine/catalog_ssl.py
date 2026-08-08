"""Declarative SSL certificate rules."""

from app.core.rule_engine.models import RuleSpec
from app.plugins.base.contracts import FindingCheckStatus

SSL_RULES: list[RuleSpec] = [
    RuleSpec(
        finding_code="SSL_EXPIRED",
        category="transport",
        condition={"path_truthy": "certificate.is_expired"},
        evidence="Certificate expired on {certificate.not_after}",
        description="The TLS certificate has passed its not-after date.",
        reference_links=("https://letsencrypt.org/",),
    ),
    RuleSpec(
        finding_code="SSL_EXPIRING_SOON",
        category="transport",
        condition={
            "op": "and",
            "conditions": [
                {"path_falsy": "certificate.is_expired"},
                {"op": "truthy", "path": "certificate.days_until_expiry"},
                {"op": "lte", "path": "certificate.days_until_expiry", "value": 30},
            ],
        },
        evidence="Certificate expires on {certificate.not_after}",
        description="The TLS certificate expires within 30 days.",
    ),
    RuleSpec(
        finding_code="SSL_EXPIRING_90",
        category="transport",
        condition={
            "op": "and",
            "conditions": [
                {"path_falsy": "certificate.is_expired"},
                {"op": "truthy", "path": "certificate.days_until_expiry"},
                {"op": "gt", "path": "certificate.days_until_expiry", "value": 30},
                {"op": "lte", "path": "certificate.days_until_expiry", "value": 90},
            ],
        },
        evidence="Certificate expires in {certificate.days_until_expiry} days on {certificate.not_after}",
        description="The TLS certificate expires within 90 days.",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        finding_code="SSL_TLS10_ENABLED",
        category="transport",
        condition={"path_contains": {"path": "protocols_accepted", "value": "TLSv1.0"}},
        evidence="TLS 1.0 handshake succeeded",
        reference_links=("https://datatracker.ietf.org/doc/rfc8996/",),
    ),
    RuleSpec(
        finding_code="SSL_TLS11_ENABLED",
        category="transport",
        condition={"path_contains": {"path": "protocols_accepted", "value": "TLSv1.1"}},
        evidence="TLS 1.1 handshake succeeded",
        reference_links=("https://datatracker.ietf.org/doc/rfc8996/",),
    ),
    RuleSpec(
        finding_code="SSL_WEAK_RSA_KEY",
        category="transport",
        condition={"path_truthy": "weak_rsa_key"},
        evidence="RSA public key length: {certificate.public_key_bits} bits",
    ),
    RuleSpec(
        finding_code="SSL_WEAK_SIGNATURE",
        category="transport",
        condition={"path_truthy": "weak_signature"},
        evidence="Signature hash algorithm: {certificate.signature_algorithm}",
    ),
    RuleSpec(
        finding_code="SSL_SELF_SIGNED",
        category="transport",
        condition={"path_truthy": "certificate.is_self_signed"},
        evidence="Issuer: {certificate.issuer}",
    ),
    RuleSpec(
        finding_code="SSL_UNTRUSTED_CHAIN",
        category="transport",
        condition={
            "op": "and",
            "conditions": [
                {"path_falsy": "chain_trusted"},
                {"path_falsy": "certificate.is_self_signed"},
            ],
        },
        evidence="Certificate chain failed validation against Mozilla CA store",
    ),
    RuleSpec(
        finding_code="SSL_HOSTNAME_MISMATCH",
        category="transport",
        condition={"path_falsy": "hostname_matches"},
        evidence="Host {host} not in CN/SAN ({certificate_sans_evidence})",
        reference_links=("https://datatracker.ietf.org/doc/html/rfc6125",),
    ),
    RuleSpec(
        finding_code="SSL_INCOMPLETE_SAN",
        category="transport",
        condition={"path_truthy": "incomplete_san_coverage"},
        evidence="Certificate missing coverage for: {incomplete_san_evidence}",
    ),
    RuleSpec(
        finding_code="SSL_NO_OCSP_STAPLING",
        category="transport",
        condition={"path_eq": {"path": "ocsp_stapling", "value": False}},
        evidence="Server did not staple an OCSP response",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        finding_code="SSL_WEAK_CIPHER",
        category="transport",
        condition={"op": "and", "conditions": [{"path_truthy": "cipher_is_weak"}, {"path_truthy": "cipher"}]},
        evidence="Negotiated cipher: {cipher.name}",
    ),
    RuleSpec(
        finding_code="SSL_ADDITIONAL_WEAK_CIPHERS",
        category="transport",
        condition={"path_nonempty": "weak_ciphers_accepted"},
        evidence="Server accepts: {weak_ciphers_evidence}",
    ),
    RuleSpec(
        finding_code="SSL_NO_FORWARD_SECRECY",
        category="transport",
        condition={"op": "and", "conditions": [{"path_truthy": "lacks_forward_secrecy"}, {"path_truthy": "cipher"}]},
        evidence="Cipher {cipher.name} does not provide forward secrecy",
    ),
    RuleSpec(
        finding_code="SSL_CT_SUSPICIOUS_ISSUER",
        category="transport",
        condition={"path_nonempty": "suspicious_ct_issuers"},
        evidence="CT log issuers: {suspicious_ct_issuers_evidence}",
        status=FindingCheckStatus.WARNING,
    ),
]
