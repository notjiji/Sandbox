"""Declarative rule catalog — update rules here without touching scanner code."""

from app.core.rule_engine.catalog_cloud import CLOUD_RULES
from app.core.rule_engine.catalog_dns import DNS_RULES
from app.core.rule_engine.catalog_ports import PORTS_RULES
from app.core.rule_engine.catalog_ssl import SSL_RULES
from app.core.rule_engine.catalog_tls import TLS_RULES
from app.core.rule_engine.catalog_whois import WHOIS_RULES
from app.core.rule_engine.models import RuleSpec
from app.plugins.base.contracts import FindingCheckStatus

HTTP_HEADERS_RULES: list[RuleSpec] = [
    RuleSpec(
        rule_code="HTTP-001",
        finding_code="HTTP_NO_CSP",
        category="headers",
        condition={"header_missing": "Content-Security-Policy"},
        evidence="Content-Security-Policy header not present on {identifier}",
        description="The Content-Security-Policy response header was not present.",
        reference_links=(
            "https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP",
            "https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html",
        ),
    ),
    RuleSpec(
        rule_code="HTTP-002",
        finding_code="HTTP_WEAK_CSP",
        category="headers",
        condition={"op": "and", "conditions": [{"path_truthy": "has_csp"}, {"path_nonempty": "weak_csp_evidence"}]},
        evidence="CSP contains: {weak_csp_evidence}",
    ),
    RuleSpec(
        rule_code="HTTP-003",
        finding_code="HTTP_CSP_BROAD_SOURCES",
        category="headers",
        condition={"op": "and", "conditions": [{"path_truthy": "has_csp"}, {"path_nonempty": "broad_csp_evidence"}]},
        evidence="CSP allows broad sources: {broad_csp_evidence}",
    ),
    RuleSpec(
        rule_code="HTTP-004",
        finding_code="HTTP_NO_HSTS",
        category="headers",
        condition={"op": "and", "conditions": [{"path_truthy": "is_https"}, {"header_missing": "Strict-Transport-Security"}]},
        evidence="Strict-Transport-Security header not present on {identifier}",
    ),
    RuleSpec(
        rule_code="HTTP-005",
        finding_code="HTTP_WEAK_HSTS",
        category="headers",
        condition={"op": "and", "conditions": [{"path_truthy": "has_hsts"}, {"path_truthy": "hsts_is_weak"}]},
        evidence="{hsts_weak_evidence}",
    ),
    RuleSpec(
        rule_code="HTTP-006",
        finding_code="HTTP_NO_REFERRER_POLICY",
        category="headers",
        condition={"header_missing": "Referrer-Policy"},
        evidence="Referrer-Policy header not present on {identifier}",
    ),
    RuleSpec(
        rule_code="HTTP-007",
        finding_code="HTTP_NO_X_FRAME_OPTIONS",
        category="headers",
        condition={"header_missing": "X-Frame-Options"},
        evidence="X-Frame-Options header not present on {identifier}",
    ),
    RuleSpec(
        rule_code="HTTP-008",
        finding_code="HTTP_NO_X_CONTENT_TYPE_OPTIONS",
        category="headers",
        condition={"header_missing": "X-Content-Type-Options"},
        evidence="X-Content-Type-Options header not present on {identifier}",
    ),
    RuleSpec(
        rule_code="HTTP-009",
        finding_code="HTTP_NO_PERMISSIONS_POLICY",
        category="headers",
        condition={"header_missing": "Permissions-Policy"},
        evidence="Permissions-Policy header not present on {identifier}",
    ),
    RuleSpec(
        rule_code="HTTP-010",
        finding_code="HTTP_SERVER_HEADER_EXPOSED",
        category="headers",
        condition={"path_truthy": "server_exposed"},
        evidence="{server_exposed_evidence}",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        rule_code="HTTP-011",
        finding_code="HTTP_TRACE_ENABLED",
        category="headers",
        condition={"path_truthy": "trace_enabled"},
        evidence="{trace_evidence}",
    ),
    RuleSpec(
        rule_code="HTTP-012",
        finding_code="HTTP_NO_HTTPS_REDIRECT",
        category="transport",
        condition={"path_eq": {"path": "http_redirects_to_https", "value": False}},
        evidence="HTTP request to {identifier} did not redirect to HTTPS",
    ),
    RuleSpec(
        rule_code="HTTP-013",
        finding_code="HTTP_INSECURE_REDIRECT",
        category="transport",
        condition={"path_nonempty": "redirect_chain_issues"},
        evidence="{redirect_chain_evidence}",
    ),
    RuleSpec(
        rule_code="HTTP-014",
        finding_code="HTTP_MIXED_CONTENT",
        category="headers",
        condition={"path_nonempty": "mixed_content_urls"},
        evidence="HTTP resources on HTTPS page: {mixed_content_evidence}",
    ),
    RuleSpec(
        rule_code="HTTP-015",
        finding_code="HTTP_WEAK_COOKIE",
        category="cookies",
        condition={"path_nonempty": "weak_cookies"},
        evidence="{weak_cookies_evidence}",
    ),
    RuleSpec(
        rule_code="HTTP-016",
        finding_code="HTTP_CORS_WILDCARD",
        category="headers",
        condition={"cors_wildcard": True},
        evidence="Access-Control-Allow-Origin is wildcard (*) on {identifier}",
        description="Wildcard CORS allows any origin to read responses from this endpoint.",
        reference_links=("https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS",),
    ),
    RuleSpec(
        rule_code="HTTP-017",
        finding_code="HTTP_CORS_CREDENTIALS_WILDCARD",
        category="headers",
        condition={"path_truthy": "cors_credentials_with_wildcard"},
        evidence="Access-Control-Allow-Credentials is true while Allow-Origin is wildcard",
    ),
    RuleSpec(
        rule_code="HTTP-018",
        finding_code="HTTP_API_SCHEMA_EXPOSED",
        category="exposure",
        condition={"path_nonempty": "api_schema_paths"},
        evidence="Public API schema discovered: {api_schema_evidence}",
        status=FindingCheckStatus.WARNING,
    ),
]

ROBOTS_RULES: list[RuleSpec] = [
    RuleSpec(
        finding_code="ROBOTS_ADMIN_PATH_DISCLOSED",
        category="exposure",
        condition={"op": "and", "conditions": [{"path_truthy": "present"}, {"path_nonempty": "admin_paths"}]},
        evidence="Admin-related paths referenced in robots.txt: {admin_paths_evidence}",
    ),
    RuleSpec(
        finding_code="ROBOTS_DEBUG_PATH_DISCLOSED",
        category="exposure",
        condition={"op": "and", "conditions": [{"path_truthy": "present"}, {"path_nonempty": "debug_paths"}]},
        evidence="Debug or test paths referenced in robots.txt: {debug_paths_evidence}",
    ),
    RuleSpec(
        finding_code="ROBOTS_SENSITIVE_PATH_DISCLOSED",
        category="exposure",
        condition={"op": "and", "conditions": [{"path_truthy": "present"}, {"path_nonempty": "sensitive_paths"}]},
        evidence="Sensitive paths referenced in robots.txt: {sensitive_paths_evidence}",
        status=FindingCheckStatus.WARNING,
    ),
]

SECURITY_TXT_RULES: list[RuleSpec] = [
    RuleSpec(
        finding_code="SECURITY_TXT_MISSING",
        category="exposure",
        condition={"path_falsy": "present"},
        evidence="/.well-known/security.txt was not found or returned an empty response",
        status=FindingCheckStatus.WARNING,
        reference_links=("https://securitytxt.org/",),
    ),
    RuleSpec(
        finding_code="SECURITY_TXT_MISSING_CONTACT",
        category="exposure",
        condition={"op": "and", "conditions": [{"path_truthy": "present"}, {"path_falsy": "has_required_contact"}]},
        evidence="security.txt is present but does not define a Contact field",
        reference_links=("https://datatracker.ietf.org/doc/html/rfc9116",),
    ),
    RuleSpec(
        finding_code="SECURITY_TXT_INVALID_CONTACT",
        category="exposure",
        condition={
            "op": "and",
            "conditions": [
                {"path_truthy": "present"},
                {"path_truthy": "has_required_contact"},
                {"path_falsy": "contact_valid"},
            ],
        },
        evidence="Invalid Contact value(s): {invalid_contacts_evidence}",
    ),
    RuleSpec(
        finding_code="SECURITY_TXT_EXPIRED",
        category="exposure",
        condition={"op": "and", "conditions": [{"path_truthy": "present"}, {"path_truthy": "expires_expired"}]},
        evidence="{expires_evidence}",
    ),
    RuleSpec(
        finding_code="SECURITY_TXT_MISSING_EXPIRES",
        category="exposure",
        condition={"op": "and", "conditions": [{"path_truthy": "present"}, {"path_falsy": "expires"}]},
        evidence="security.txt does not define an Expires field",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        finding_code="SECURITY_TXT_INVALID_ENCRYPTION",
        category="exposure",
        condition={
            "op": "and",
            "conditions": [
                {"path_truthy": "present"},
                {"path_nonempty": "encryption"},
                {"path_falsy": "encryption_valid"},
            ],
        },
        evidence="Invalid Encryption URI(s): {invalid_encryption_evidence}",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        finding_code="SECURITY_TXT_INVALID_CANONICAL",
        category="exposure",
        condition={
            "op": "or",
            "conditions": [
                {
                    "op": "and",
                    "conditions": [{"path_truthy": "present"}, {"path_nonempty": "canonical"}, {"path_falsy": "canonical_valid"}],
                },
                {
                    "op": "and",
                    "conditions": [
                        {"path_truthy": "present"},
                        {"path_nonempty": "canonical"},
                        {"path_eq": {"path": "canonical_matches", "value": False}},
                    ],
                },
            ],
        },
        evidence="{canonical_evidence}",
        status=FindingCheckStatus.WARNING,
    ),
]

PLUGIN_RULES: dict[str, list[RuleSpec]] = {
    "http_headers": HTTP_HEADERS_RULES,
    "robots": ROBOTS_RULES,
    "security_txt": SECURITY_TXT_RULES,
    "dns": DNS_RULES,
    "ssl": SSL_RULES,
    "ports": PORTS_RULES,
    "whois": WHOIS_RULES,
    "tls": TLS_RULES,
    "cloud": CLOUD_RULES,
}


def get_plugin_rules(plugin_id: str) -> list[RuleSpec]:
    return list(PLUGIN_RULES.get(plugin_id, []))
