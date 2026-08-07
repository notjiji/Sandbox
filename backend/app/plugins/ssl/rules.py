"""SSL rules — evaluated by the declarative rule engine."""

from collections.abc import Callable

from app.core.rule_engine.catalog import get_plugin_rules
from app.core.rule_engine.engine import evaluate_plugin_rules
from app.plugins.base.plugin import ScanTarget
from app.plugins.ssl.schemas import SslParsedData

RuleFn = Callable[[SslParsedData, ScanTarget, str], object | None]


def _single_rule(finding_code: str) -> RuleFn:
    rules = [rule for rule in get_plugin_rules("ssl") if rule.finding_code == finding_code]

    def evaluate(parsed: SslParsedData, asset: ScanTarget, plugin_id: str):
        findings = evaluate_plugin_rules("ssl", parsed, asset, rules=rules)
        return findings[0] if findings else None

    return evaluate


rule_expired_certificate = _single_rule("SSL_EXPIRED")
rule_expiring_soon = _single_rule("SSL_EXPIRING_SOON")
rule_tls10_enabled = _single_rule("SSL_TLS10_ENABLED")
rule_tls11_enabled = _single_rule("SSL_TLS11_ENABLED")
rule_weak_rsa_key = _single_rule("SSL_WEAK_RSA_KEY")
rule_weak_signature = _single_rule("SSL_WEAK_SIGNATURE")
rule_self_signed = _single_rule("SSL_SELF_SIGNED")
rule_untrusted_chain = _single_rule("SSL_UNTRUSTED_CHAIN")
rule_hostname_mismatch = _single_rule("SSL_HOSTNAME_MISMATCH")
rule_incomplete_san_coverage = _single_rule("SSL_INCOMPLETE_SAN")
rule_no_ocsp_stapling = _single_rule("SSL_NO_OCSP_STAPLING")
rule_weak_cipher_negotiated = _single_rule("SSL_WEAK_CIPHER")
rule_additional_weak_ciphers = _single_rule("SSL_ADDITIONAL_WEAK_CIPHERS")
rule_no_forward_secrecy = _single_rule("SSL_NO_FORWARD_SECRECY")
rule_ct_suspicious_issuer = _single_rule("SSL_CT_SUSPICIOUS_ISSUER")


def evaluate_rules(parsed: SslParsedData, asset: ScanTarget, *, plugin_id: str):
    return evaluate_plugin_rules("ssl", parsed, asset)
