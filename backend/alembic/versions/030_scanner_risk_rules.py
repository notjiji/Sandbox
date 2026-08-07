"""Seed scanner risk rules for DNS, HTTP, and SSL plugins

Revision ID: 030
Revises: 029
Create Date: 2026-08-07

"""
from typing import Sequence, Union

from alembic import op

revision: str = "030"
down_revision: Union[str, None] = "029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SCANNER_RISK_RULES = """
INSERT INTO risk_rules (id, plugin, finding_code, title, description, severity, score, enabled)
VALUES
    (gen_random_uuid(), 'dns', 'DNS_MISSING_SPF', 'Missing SPF Record', 'No SPF record found for the domain.', 'medium', 10, true),
    (gen_random_uuid(), 'dns', 'DNS_MULTIPLE_SPF', 'Multiple SPF Records', 'More than one SPF TXT record was found.', 'high', 25, true),
    (gen_random_uuid(), 'dns', 'DNS_SPF_TOO_MANY_LOOKUPS', 'SPF Exceeds DNS Lookup Limit', 'SPF record exceeds the 10 DNS lookup limit.', 'medium', 12, true),
    (gen_random_uuid(), 'dns', 'DNS_WEAK_SPF', 'Weak SPF Policy', 'SPF record uses a permissive or invalid policy.', 'medium', 15, true),
    (gen_random_uuid(), 'dns', 'DNS_MISSING_DMARC', 'Missing DMARC Record', 'No DMARC TXT record found at _dmarc.', 'medium', 12, true),
    (gen_random_uuid(), 'dns', 'DNS_WEAK_DMARC', 'Weak DMARC Policy', 'DMARC policy is set to p=none.', 'medium', 15, true),
    (gen_random_uuid(), 'dns', 'DNS_DMARC_MISSING_RUA', 'DMARC Missing Reporting Address', 'DMARC record lacks rua/ruf reporting tags.', 'low', 5, true),
    (gen_random_uuid(), 'dns', 'DNS_MISSING_DKIM', 'No DKIM Record Found', 'No DKIM TXT records found at common or CT-discovered selectors.', 'low', 5, true),
    (gen_random_uuid(), 'dns', 'DNS_DNSSEC_DISABLED', 'DNSSEC Not Enabled', 'No DNSKEY and DS records found for the domain.', 'medium', 15, true),
    (gen_random_uuid(), 'dns', 'DNS_DNSSEC_INCOMPLETE', 'Incomplete DNSSEC Configuration', 'DNSKEY records exist but DS records are missing.', 'medium', 18, true),
    (gen_random_uuid(), 'dns', 'DNS_MISSING_CAA', 'Missing CAA Records', 'No CAA records restrict certificate issuance.', 'low', 8, true),
    (gen_random_uuid(), 'dns', 'DNS_MISSING_MTA_STS', 'Missing MTA-STS Policy', 'Domain has MX records but no MTA-STS policy.', 'low', 5, true),
    (gen_random_uuid(), 'dns', 'DNS_MISSING_TLS_RPT', 'Missing TLS-RPT Record', 'Domain has MX records but no TLS-RPT record.', 'low', 3, true),
    (gen_random_uuid(), 'dns', 'DNS_SUBDOMAIN_TAKEOVER', 'Potential Subdomain Takeover', 'Dangling CNAME or HTTP takeover fingerprint detected.', 'high', 40, true),
    (gen_random_uuid(), 'dns', 'DNS_ZONE_TRANSFER', 'DNS Zone Transfer Allowed', 'Unrestricted AXFR zone transfer succeeded.', 'high', 35, true),
    (gen_random_uuid(), 'dns', 'DNS_MX_MISCONFIGURED', 'MX Host Does Not Resolve', 'An MX hostname has no A/AAAA records.', 'high', 30, true),
    (gen_random_uuid(), 'dns', 'DNS_WILDCARD_DETECTED', 'Wildcard DNS Detected', 'Random subdomain probe resolved unexpectedly.', 'low', 5, true),
    (gen_random_uuid(), 'dns', 'DNS_LOW_TTL', 'Low DNS TTL', 'Minimum TTL is below recommended threshold.', 'low', 3, true),
    (gen_random_uuid(), 'dns', 'DNS_RESOLVER_DISCREPANCY', 'DNS Resolver Discrepancy', 'Record sets differ across public resolvers.', 'medium', 12, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_NO_CSP', 'Missing Content-Security-Policy', 'Response lacks a Content-Security-Policy header.', 'high', 25, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_WEAK_CSP', 'Weak Content Security Policy', 'CSP contains unsafe-inline, unsafe-eval, or wildcards.', 'medium', 15, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_NO_HSTS', 'Missing Strict-Transport-Security', 'Response lacks an HSTS header.', 'high', 25, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_WEAK_HSTS', 'Weak HSTS Configuration', 'HSTS max-age is below recommended threshold.', 'medium', 12, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_NO_REFERRER_POLICY', 'Missing Referrer Policy', 'Response lacks a Referrer-Policy header.', 'medium', 10, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_NO_X_FRAME_OPTIONS', 'Missing X-Frame-Options', 'Response lacks clickjacking protection header.', 'medium', 12, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_NO_X_CONTENT_TYPE_OPTIONS', 'Missing X-Content-Type-Options', 'Response lacks MIME-sniffing protection header.', 'medium', 10, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_NO_PERMISSIONS_POLICY', 'Missing Permissions-Policy', 'Response lacks a Permissions-Policy header.', 'low', 5, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_SERVER_HEADER_EXPOSED', 'Server Technology Header Exposed', 'Server or framework identifiers are exposed.', 'low', 3, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_TRACE_ENABLED', 'HTTP TRACE Method Enabled', 'Server accepts TRACE requests.', 'medium', 15, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_NO_HTTPS_REDIRECT', 'HTTP Does Not Redirect to HTTPS', 'Plain HTTP is served without HTTPS redirect.', 'high', 30, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_INSECURE_REDIRECT', 'Insecure Redirect Chain', 'Redirect chain downgrades from HTTPS to HTTP.', 'high', 28, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_MIXED_CONTENT', 'Mixed Content Detected', 'HTTPS page loads resources over HTTP.', 'medium', 12, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_WEAK_COOKIE', 'Weak Session Cookie Configuration', 'Session cookies lack Secure/HttpOnly/SameSite.', 'high', 25, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_MISSING_SECURITY_TXT', 'Missing security.txt', 'No valid /.well-known/security.txt was found.', 'low', 3, true),
    (gen_random_uuid(), 'ssl', 'SSL_EXPIRED', 'Expired SSL Certificate', 'The TLS certificate is expired.', 'critical', 50, true),
    (gen_random_uuid(), 'ssl', 'SSL_EXPIRING_SOON', 'Certificate Expiring Soon', 'The TLS certificate expires within 30 days.', 'medium', 15, true),
    (gen_random_uuid(), 'ssl', 'SSL_TLS10_ENABLED', 'TLS 1.0 Enabled', 'Legacy TLS 1.0 is still enabled.', 'high', 30, true),
    (gen_random_uuid(), 'ssl', 'SSL_TLS11_ENABLED', 'TLS 1.1 Enabled', 'Deprecated TLS 1.1 is still enabled.', 'high', 28, true),
    (gen_random_uuid(), 'ssl', 'SSL_WEAK_RSA_KEY', 'Weak RSA Key Length', 'Certificate uses an RSA key shorter than 2048 bits.', 'high', 35, true),
    (gen_random_uuid(), 'ssl', 'SSL_WEAK_SIGNATURE', 'Weak Certificate Signature Algorithm', 'Certificate is signed with MD5 or SHA-1.', 'high', 32, true),
    (gen_random_uuid(), 'ssl', 'SSL_SELF_SIGNED', 'Self-Signed Certificate', 'Certificate issuer matches the subject.', 'high', 35, true),
    (gen_random_uuid(), 'ssl', 'SSL_UNTRUSTED_CHAIN', 'Untrusted Certificate Chain', 'Certificate chain failed trust validation.', 'high', 38, true),
    (gen_random_uuid(), 'ssl', 'SSL_HOSTNAME_MISMATCH', 'Certificate Hostname Mismatch', 'Certificate does not cover the scanned hostname.', 'high', 30, true),
    (gen_random_uuid(), 'ssl', 'SSL_INCOMPLETE_SAN', 'Incomplete Certificate SAN Coverage', 'Certificate missing apex or www SAN coverage.', 'medium', 12, true),
    (gen_random_uuid(), 'ssl', 'SSL_NO_OCSP_STAPLING', 'OCSP Stapling Not Enabled', 'Server did not staple an OCSP response.', 'low', 5, true),
    (gen_random_uuid(), 'ssl', 'SSL_WEAK_CIPHER', 'Weak Cipher Suite Negotiated', 'Server negotiated a weak cipher suite.', 'high', 35, true),
    (gen_random_uuid(), 'ssl', 'SSL_ADDITIONAL_WEAK_CIPHERS', 'Additional Weak Ciphers Accepted', 'Server accepts additional legacy cipher suites.', 'medium', 20, true),
    (gen_random_uuid(), 'ssl', 'SSL_NO_FORWARD_SECRECY', 'No Forward Secrecy', 'Negotiated cipher does not provide forward secrecy.', 'medium', 18, true)
ON CONFLICT (plugin, finding_code) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    severity = EXCLUDED.severity,
    score = EXCLUDED.score,
    enabled = EXCLUDED.enabled,
    updated_at = now()
"""


def upgrade() -> None:
    op.execute(_SCANNER_RISK_RULES)


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM risk_rules
        WHERE plugin IN ('dns', 'http_headers', 'ssl')
          AND finding_code IN (
            'DNS_MULTIPLE_SPF', 'DNS_SPF_TOO_MANY_LOOKUPS', 'DNS_WEAK_SPF',
            'DNS_MISSING_DMARC', 'DNS_WEAK_DMARC', 'DNS_DMARC_MISSING_RUA',
            'DNS_MISSING_DKIM', 'DNS_DNSSEC_DISABLED', 'DNS_DNSSEC_INCOMPLETE',
            'DNS_MISSING_CAA', 'DNS_MISSING_MTA_STS', 'DNS_MISSING_TLS_RPT',
            'DNS_SUBDOMAIN_TAKEOVER', 'DNS_ZONE_TRANSFER', 'DNS_MX_MISCONFIGURED',
            'DNS_WILDCARD_DETECTED', 'DNS_LOW_TTL', 'DNS_RESOLVER_DISCREPANCY',
            'HTTP_WEAK_CSP', 'HTTP_WEAK_HSTS', 'HTTP_NO_REFERRER_POLICY',
            'HTTP_NO_X_FRAME_OPTIONS', 'HTTP_NO_X_CONTENT_TYPE_OPTIONS',
            'HTTP_NO_PERMISSIONS_POLICY', 'HTTP_SERVER_HEADER_EXPOSED',
            'HTTP_TRACE_ENABLED', 'HTTP_NO_HTTPS_REDIRECT', 'HTTP_INSECURE_REDIRECT',
            'HTTP_MIXED_CONTENT', 'HTTP_WEAK_COOKIE', 'HTTP_MISSING_SECURITY_TXT',
            'SSL_EXPIRING_SOON', 'SSL_TLS11_ENABLED', 'SSL_WEAK_RSA_KEY',
            'SSL_WEAK_SIGNATURE', 'SSL_SELF_SIGNED', 'SSL_UNTRUSTED_CHAIN',
            'SSL_HOSTNAME_MISMATCH', 'SSL_INCOMPLETE_SAN', 'SSL_NO_OCSP_STAPLING',
            'SSL_WEAK_CIPHER', 'SSL_ADDITIONAL_WEAK_CIPHERS', 'SSL_NO_FORWARD_SECRECY'
          )
        """
    )
