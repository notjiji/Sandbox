"""Independent SSL/TLS security rules."""

from collections.abc import Callable

from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.ssl.schemas import SslParsedData

RuleFn = Callable[[SslParsedData, ScanTarget, str], ScanFinding | None]

_EXPIRY_WARNING_DAYS = 30
_WEAK_RSA_BITS = 2048
_WEAK_SIGNATURES = {"md5", "sha1"}


def rule_expired_certificate(parsed: SslParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.certificate.is_expired:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="SSL_EXPIRED",
        asset_id=asset.asset_id,
        title="Expired SSL Certificate",
        description="The TLS certificate has passed its not-after date.",
        category="transport",
        evidence=f"Certificate expired on {parsed.certificate.not_after}",
        recommendation="Renew and install a valid TLS certificate immediately.",
        reference_links=["https://letsencrypt.org/"],
        severity=FindingSeverity.CRITICAL,
        status=FindingCheckStatus.FAILED,
    )


def rule_expiring_soon(parsed: SslParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    days = parsed.certificate.days_until_expiry
    if days is None or parsed.certificate.is_expired or days > _EXPIRY_WARNING_DAYS:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="SSL_EXPIRING_SOON",
        asset_id=asset.asset_id,
        title="Certificate Expiring Soon",
        description=f"The TLS certificate expires in {days} days.",
        category="transport",
        evidence=f"Certificate expires on {parsed.certificate.not_after}",
        recommendation="Renew the certificate before expiry to avoid service disruption.",
        severity=FindingSeverity.MEDIUM,
        status=FindingCheckStatus.WARNING,
    )


def rule_tls10_enabled(parsed: SslParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if "TLSv1.0" not in parsed.protocols_accepted:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="SSL_TLS10_ENABLED",
        asset_id=asset.asset_id,
        title="TLS 1.0 Enabled",
        description="The endpoint accepts deprecated TLS 1.0 connections.",
        category="transport",
        evidence="TLS 1.0 handshake succeeded",
        recommendation="Disable TLS 1.0 and enforce TLS 1.2 or higher.",
        reference_links=["https://datatracker.ietf.org/doc/rfc8996/"],
        severity=FindingSeverity.HIGH,
        status=FindingCheckStatus.FAILED,
    )


def rule_tls11_enabled(parsed: SslParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if "TLSv1.1" not in parsed.protocols_accepted:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="SSL_TLS11_ENABLED",
        asset_id=asset.asset_id,
        title="TLS 1.1 Enabled",
        description="The endpoint accepts deprecated TLS 1.1 connections.",
        category="transport",
        evidence="TLS 1.1 handshake succeeded",
        recommendation="Disable TLS 1.1 and enforce TLS 1.2 or higher.",
        reference_links=["https://datatracker.ietf.org/doc/rfc8996/"],
        severity=FindingSeverity.HIGH,
        status=FindingCheckStatus.FAILED,
    )


def rule_weak_rsa_key(parsed: SslParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    cert = parsed.certificate
    if cert.public_key_algorithm != "RSA" or cert.public_key_bits is None:
        return None
    if cert.public_key_bits >= _WEAK_RSA_BITS:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="SSL_WEAK_RSA_KEY",
        asset_id=asset.asset_id,
        title="Weak RSA Key Length",
        description=f"The certificate uses a {cert.public_key_bits}-bit RSA key.",
        category="transport",
        evidence=f"RSA public key length: {cert.public_key_bits} bits",
        recommendation="Reissue the certificate with at least a 2048-bit RSA key (4096 preferred).",
        reference_links=["https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html"],
        severity=FindingSeverity.HIGH,
        status=FindingCheckStatus.FAILED,
    )


def rule_weak_signature(parsed: SslParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    algorithm = (parsed.certificate.signature_algorithm or "").lower()
    if not any(weak in algorithm for weak in _WEAK_SIGNATURES):
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="SSL_WEAK_SIGNATURE",
        asset_id=asset.asset_id,
        title="Weak Certificate Signature Algorithm",
        description=f"The certificate is signed with {parsed.certificate.signature_algorithm}.",
        category="transport",
        evidence=f"Signature hash algorithm: {parsed.certificate.signature_algorithm}",
        recommendation="Reissue the certificate using SHA-256 or stronger.",
        severity=FindingSeverity.HIGH,
        status=FindingCheckStatus.FAILED,
    )


def rule_self_signed(parsed: SslParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.certificate.is_self_signed:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="SSL_SELF_SIGNED",
        asset_id=asset.asset_id,
        title="Self-Signed Certificate",
        description="The certificate issuer matches the subject, indicating it is self-signed.",
        category="transport",
        evidence=f"Issuer: {parsed.certificate.issuer}",
        recommendation="Use a certificate signed by a trusted public or private CA.",
        severity=FindingSeverity.HIGH,
        status=FindingCheckStatus.FAILED,
    )


def rule_hostname_mismatch(parsed: SslParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.hostname_matches:
        return None
    sans = ", ".join(parsed.certificate.sans) or parsed.certificate.common_name or "none"
    return scan_finding(
        plugin=plugin_id,
        rule_id="SSL_HOSTNAME_MISMATCH",
        asset_id=asset.asset_id,
        title="Certificate Hostname Mismatch",
        description="The certificate does not cover the scanned hostname.",
        category="transport",
        evidence=f"Host {parsed.host} not in CN/SAN ({sans})",
        recommendation="Reissue the certificate with the correct Common Name or Subject Alternative Names.",
        reference_links=["https://datatracker.ietf.org/doc/html/rfc6125"],
        severity=FindingSeverity.HIGH,
        status=FindingCheckStatus.FAILED,
    )


def rule_untrusted_chain(parsed: SslParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.chain_trusted or parsed.certificate.is_self_signed:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="SSL_UNTRUSTED_CHAIN", asset_id=asset.asset_id,
        title="Untrusted Certificate Chain", category="transport",
        evidence="Certificate chain failed validation against Mozilla CA store",
        recommendation="Install a certificate signed by a publicly trusted CA with complete chain.",
        severity=FindingSeverity.HIGH, status=FindingCheckStatus.FAILED,
    )


def rule_no_ocsp_stapling(parsed: SslParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.ocsp_stapling is not False:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="SSL_NO_OCSP_STAPLING", asset_id=asset.asset_id,
        title="OCSP Stapling Not Enabled", category="transport",
        evidence="Server did not staple an OCSP response",
        recommendation="Enable OCSP stapling to improve revocation checking performance and privacy.",
        severity=FindingSeverity.LOW, status=FindingCheckStatus.WARNING,
    )


def rule_weak_cipher_negotiated(parsed: SslParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.cipher_is_weak or parsed.cipher is None:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="SSL_WEAK_CIPHER", asset_id=asset.asset_id,
        title="Weak Cipher Suite Negotiated", category="transport",
        evidence=f"Negotiated cipher: {parsed.cipher.name}",
        recommendation="Disable weak cipher suites and prefer AEAD ciphers with forward secrecy.",
        severity=FindingSeverity.HIGH, status=FindingCheckStatus.FAILED,
    )


def rule_additional_weak_ciphers(parsed: SslParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.weak_ciphers_accepted:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="SSL_ADDITIONAL_WEAK_CIPHERS", asset_id=asset.asset_id,
        title="Additional Weak Ciphers Accepted", category="transport",
        evidence=f"Server accepts: {', '.join(parsed.weak_ciphers_accepted)}",
        recommendation="Disable legacy cipher suites at the server configuration level.",
        severity=FindingSeverity.MEDIUM, status=FindingCheckStatus.FAILED,
    )


def rule_no_forward_secrecy(parsed: SslParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.lacks_forward_secrecy or parsed.cipher is None:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="SSL_NO_FORWARD_SECRECY", asset_id=asset.asset_id,
        title="No Forward Secrecy", category="transport",
        evidence=f"Cipher {parsed.cipher.name} does not provide forward secrecy",
        recommendation="Prefer ECDHE/DHE cipher suites.",
        severity=FindingSeverity.MEDIUM, status=FindingCheckStatus.FAILED,
    )


def rule_incomplete_san_coverage(parsed: SslParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.san_covers_apex and parsed.san_covers_www:
        return None
    missing = []
    if not parsed.san_covers_apex:
        missing.append("apex")
    if not parsed.san_covers_www:
        missing.append("www")
    return scan_finding(
        plugin=plugin_id, rule_id="SSL_INCOMPLETE_SAN", asset_id=asset.asset_id,
        title="Incomplete Certificate SAN Coverage", category="transport",
        evidence=f"Certificate missing coverage for: {', '.join(missing)}",
        recommendation="Include both apex and www hostnames in the certificate SAN list.",
        severity=FindingSeverity.MEDIUM, status=FindingCheckStatus.FAILED,
    )


RULES: list[RuleFn] = [
    rule_expired_certificate,
    rule_expiring_soon,
    rule_tls10_enabled,
    rule_tls11_enabled,
    rule_weak_rsa_key,
    rule_weak_signature,
    rule_self_signed,
    rule_untrusted_chain,
    rule_hostname_mismatch,
    rule_incomplete_san_coverage,
    rule_no_ocsp_stapling,
    rule_weak_cipher_negotiated,
    rule_additional_weak_ciphers,
    rule_no_forward_secrecy,
]


def evaluate_rules(parsed: SslParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    for rule in RULES:
        finding = rule(parsed, asset, plugin_id)
        if finding is not None:
            findings.append(finding)
    return findings
