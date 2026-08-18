# Risk rule catalog

Weights and severities below are the **seeded `risk_rules` table** after Alembic through `042_alerts_vs_findings` (later `ON CONFLICT` updates win). Source files: `backend/alembic/versions/018_risk_rules.py`, `030`–`035`, `041`, `042`.

**Weight** = `risk_rules.score`, stored on the finding as `risk_score` and subtracted from 100 while the finding is `open`. See [scoring-model.md](./scoring-model.md).

**Evidence** is the `RuleSpec.evidence` template from `backend/app/core/rule_engine/catalog*.py` (what the plugin records when the rule matches). Monitoring evidence comes from the agent finding engine, not `RuleSpec`.

Disabled rows remain in the database but do not apply when `enabled=false`.

---

## HTTP headers (`http_headers`)

| Rule | Code | Severity | Weight | Evidence |
|------|------|----------|--------:|----------|
| Missing Content-Security-Policy | `HTTP_NO_CSP` | high | 25 | `Content-Security-Policy header not present on {identifier}` |
| Weak Content Security Policy | `HTTP_WEAK_CSP` | medium | 15 | `CSP contains: {weak_csp_evidence}` |
| Overly Broad CSP Sources | `HTTP_CSP_BROAD_SOURCES` | medium | 12 | `CSP allows broad sources: {broad_csp_evidence}` |
| Missing Strict-Transport-Security | `HTTP_NO_HSTS` | high | 25 | `Strict-Transport-Security header not present on {identifier}` |
| Weak HSTS Configuration | `HTTP_WEAK_HSTS` | medium | 12 | `{hsts_weak_evidence}` |
| Missing Referrer Policy | `HTTP_NO_REFERRER_POLICY` | medium | 10 | `Referrer-Policy header not present on {identifier}` |
| Missing X-Frame-Options | `HTTP_NO_X_FRAME_OPTIONS` | medium | 12 | `X-Frame-Options header not present on {identifier}` |
| Missing X-Content-Type-Options | `HTTP_NO_X_CONTENT_TYPE_OPTIONS` | medium | 10 | `X-Content-Type-Options header not present on {identifier}` |
| Missing Permissions-Policy | `HTTP_NO_PERMISSIONS_POLICY` | low | 5 | `Permissions-Policy header not present on {identifier}` |
| Server Technology Header Exposed | `HTTP_SERVER_HEADER_EXPOSED` | low | 3 | `{server_exposed_evidence}` |
| HTTP TRACE Method Enabled | `HTTP_TRACE_ENABLED` | medium | 15 | `{trace_evidence}` |
| HTTP Does Not Redirect to HTTPS | `HTTP_NO_HTTPS_REDIRECT` | high | 30 | `HTTP request to {identifier} did not redirect to HTTPS` |
| Insecure Redirect Chain | `HTTP_INSECURE_REDIRECT` | high | 28 | `{redirect_chain_evidence}` |
| Mixed Content Detected | `HTTP_MIXED_CONTENT` | medium | 12 | `HTTP resources on HTTPS page: {mixed_content_evidence}` |
| Weak Session Cookie Configuration | `HTTP_WEAK_COOKIE` | high | 25 | `{weak_cookies_evidence}` |
| Missing security.txt (legacy) | `HTTP_MISSING_SECURITY_TXT` | low | 3 | **disabled** — superseded by `security_txt` plugin |

Catalog-only (no `risk_rules` row → fallback **medium / 15**): `HTTP_CORS_WILDCARD`, `HTTP_CORS_CREDENTIALS_WILDCARD`, `HTTP_API_SCHEMA_EXPOSED`.

---

## SSL / TLS (`ssl`, `tls`)

TLS plugin evaluates `SSL_RULES + TLS_RULES`. Seeded rows use plugin `ssl`.

| Rule | Code | Severity | Weight | Evidence |
|------|------|----------|--------:|----------|
| Expired SSL Certificate | `SSL_EXPIRED` | critical | 50 | `Certificate expired on {certificate.not_after}` |
| Certificate Expiring Soon (≤30 days) | `SSL_EXPIRING_SOON` | medium | 15 | `Certificate expires on {certificate.not_after}` |
| TLS 1.0 Enabled | `SSL_TLS10_ENABLED` | high | 30 | `TLS 1.0 handshake succeeded` |
| TLS 1.1 Enabled | `SSL_TLS11_ENABLED` | high | 28 | `TLS 1.1 handshake succeeded` |
| Weak RSA Key Length | `SSL_WEAK_RSA_KEY` | high | 35 | `RSA public key length: {certificate.public_key_bits} bits` |
| Weak Certificate Signature Algorithm | `SSL_WEAK_SIGNATURE` | high | 32 | `Signature hash algorithm: {certificate.signature_algorithm}` |
| Self-Signed Certificate | `SSL_SELF_SIGNED` | high | 35 | `Issuer: {certificate.issuer}` |
| Untrusted Certificate Chain | `SSL_UNTRUSTED_CHAIN` | high | 38 | `Certificate chain failed validation against Mozilla CA store` |
| Certificate Hostname Mismatch | `SSL_HOSTNAME_MISMATCH` | high | 30 | `Host {host} not in CN/SAN ({certificate_sans_evidence})` |
| Incomplete Certificate SAN Coverage | `SSL_INCOMPLETE_SAN` | medium | 12 | `Certificate missing coverage for: {incomplete_san_evidence}` |
| OCSP Stapling Not Enabled | `SSL_NO_OCSP_STAPLING` | low | 5 | `Server did not staple an OCSP response` |
| Weak Cipher Suite Negotiated | `SSL_WEAK_CIPHER` | high | 35 | `Negotiated cipher: {cipher.name}` |
| Additional Weak Ciphers Accepted | `SSL_ADDITIONAL_WEAK_CIPHERS` | medium | 20 | `Server accepts: {weak_ciphers_evidence}` |
| No Forward Secrecy | `SSL_NO_FORWARD_SECRECY` | medium | 18 | `Cipher {cipher.name} does not provide forward secrecy` |
| Suspicious CT Issuer | `SSL_CT_SUSPICIOUS_ISSUER` | medium | 15 | `CT log issuers: {suspicious_ct_issuers_evidence}` |

Catalog-only (fallback medium / 15): `SSL_EXPIRING_90` (30–90 days), `TLS_NO_HSTS` (`TLS is enabled on {host} but no Strict-Transport-Security header was observed`).

---

## DNS (`dns`)

| Rule | Code | Severity | Weight | Evidence |
|------|------|----------|--------:|----------|
| Missing SPF Record | `DNS_MISSING_SPF` | medium | 10 | `No TXT record containing v=spf1` |
| Multiple SPF Records | `DNS_MULTIPLE_SPF` | high | 25 | `Found {spf_record_count} SPF records` |
| SPF Exceeds DNS Lookup Limit | `DNS_SPF_TOO_MANY_LOOKUPS` | medium | 12 | `Estimated {spf_lookup_count} SPF DNS lookups (limit 10)` |
| Weak SPF Policy | `DNS_WEAK_SPF` | medium | 15 | `{spf_record}` |
| Missing DMARC Record | `DNS_MISSING_DMARC` | medium | 12 | `No v=DMARC1 TXT at _dmarc.{domain}` |
| Weak DMARC Policy | `DNS_WEAK_DMARC` | medium | 15 | `DMARC p={dmarc_policy}` |
| DMARC Missing Reporting Address | `DNS_DMARC_MISSING_RUA` | low | 5 | `No rua or ruf tag in DMARC record` |
| No DKIM Record Found | `DNS_MISSING_DKIM` | low | 5 | `No DKIM TXT at common selectors` |
| DNSSEC Not Enabled | `DNS_DNSSEC_DISABLED` | medium | 15 | `No DNSKEY+DS records for {domain}` |
| Incomplete DNSSEC Configuration | `DNS_DNSSEC_INCOMPLETE` | medium | 18 | `DNSKEY records found but no DS records in parent zone` |
| DNSSEC Validation Failed | `DNS_DNSSEC_INVALID` | high | 28 | `DNSSEC records present but chain failed validation...` |
| Missing CAA Records | `DNS_MISSING_CAA` | low | 8 | `No CAA records for {domain}` |
| Missing MTA-STS Policy | `DNS_MISSING_MTA_STS` | low | 5 | `Domain has MX records but no _mta-sts TXT record` |
| Missing TLS-RPT Record | `DNS_MISSING_TLS_RPT` | low | 3 | `Domain has MX records but no _smtp._tls TXT record` |
| Potential Subdomain Takeover | `DNS_SUBDOMAIN_TAKEOVER` | high | 40 | `{subdomain_takeover_evidence}` |
| DNS Zone Transfer Allowed | `DNS_ZONE_TRANSFER` | high | 35 | `AXFR succeeded for {domain}` |
| MX Host Does Not Resolve | `DNS_MX_MISCONFIGURED` | high | 30 | `MX hosts without A records: {mx_misconfigured_evidence}` |
| Wildcard DNS Detected | `DNS_WILDCARD_DETECTED` | low | 5 | `Random subdomain probe resolved for {domain}` |
| Low DNS TTL | `DNS_LOW_TTL` | low | 3 | `Minimum TTL: {minimum_ttl}s` |
| DNS Resolver Discrepancy | `DNS_RESOLVER_DISCREPANCY` | medium | 12 | `{resolver_discrepancy_evidence}` |

Catalog-only (fallback medium / 15): `DNS_MISSING_BIMI`.

---

## WHOIS (`whois`)

| Rule | Code | Severity | Weight | Evidence |
|------|------|----------|--------:|----------|
| Domain Registration Expired | `WHOIS_EXPIRED` | critical | 45 | `WHOIS expiration date: {expires_evidence}` |
| Domain Expiring Soon | `WHOIS_EXPIRING_SOON` | low | 5 | `Registration expires in {days_until_expiry} days` |
| WHOIS Privacy Disabled | `WHOIS_PRIVACY_DISABLED` | low | 4 | `Registrant contact details appear publicly visible in WHOIS` |
| Unknown Domain Registrar | `WHOIS_UNKNOWN_REGISTRAR` | medium | 8 | `Registrar field missing or unknown for {domain}` |

---

## Ports (`ports`)

| Rule | Code | Severity | Weight | Evidence |
|------|------|----------|--------:|----------|
| FTP Port Open | `PORT_FTP_OPEN` | medium | 18 | `{port_21_evidence}` (port 21) |
| Telnet Port Open | `PORT_TELNET_OPEN` | critical | 45 | `{port_23_evidence}` (port 23) |
| RDP Exposed | `PORT_RDP_EXPOSED` | high | 35 | `{port_3389_evidence}` (port 3389) |
| MySQL Publicly Exposed | `PORT_MYSQL_PUBLIC` | high | 32 | `{port_3306_evidence}` (port 3306) |
| Redis Publicly Exposed | `PORT_REDIS_PUBLIC` | high | 34 | `{port_6379_evidence}` (port 6379) |
| MongoDB Publicly Exposed | `PORT_MONGODB_PUBLIC` | high | 36 | `{port_27017_evidence}` (port 27017) |
| SMB Port Open | `PORT_SMB_OPEN` | high | 30 | Seeded in `031`; **not** in current `catalog_ports.py` — will not emit until the catalog includes it |
| RDP Port Open (legacy) | `PORT_RDP_OPEN` | high | 35 | **disabled** — replaced by `PORT_RDP_EXPOSED` |

---

## robots.txt (`robots`)

| Rule | Code | Severity | Weight | Evidence |
|------|------|----------|--------:|----------|
| Admin Paths Disclosed | `ROBOTS_ADMIN_PATH_DISCLOSED` | medium | 12 | `Admin-related paths referenced in robots.txt: {admin_paths_evidence}` |
| Debug Paths Disclosed | `ROBOTS_DEBUG_PATH_DISCLOSED` | high | 22 | `Debug or test paths referenced in robots.txt: {debug_paths_evidence}` |
| Sensitive Paths Disclosed | `ROBOTS_SENSITIVE_PATH_DISCLOSED` | low | 6 | `Sensitive paths referenced in robots.txt: {sensitive_paths_evidence}` |

---

## security.txt (`security_txt`)

| Rule | Code | Severity | Weight | Evidence |
|------|------|----------|--------:|----------|
| Missing security.txt | `SECURITY_TXT_MISSING` | low | 3 | `/.well-known/security.txt was not found or returned an empty response` |
| Missing Contact | `SECURITY_TXT_MISSING_CONTACT` | medium | 10 | `security.txt is present but does not define a Contact field` |
| Invalid Contact | `SECURITY_TXT_INVALID_CONTACT` | medium | 10 | `Invalid Contact value(s): {invalid_contacts_evidence}` |
| Expired | `SECURITY_TXT_EXPIRED` | medium | 12 | `{expires_evidence}` |
| Missing Expires | `SECURITY_TXT_MISSING_EXPIRES` | low | 4 | `security.txt does not define an Expires field` |
| Invalid Encryption | `SECURITY_TXT_INVALID_ENCRYPTION` | low | 4 | `Invalid Encryption URI(s): {invalid_encryption_evidence}` |
| Invalid Canonical | `SECURITY_TXT_INVALID_CANONICAL` | low | 4 | `{canonical_evidence}` |

---

## Cookies (`cookies`)

Declarative catalog exists (`catalog_cookies.py`). There is **no** Alembic seed for these codes, so weights fall back to **medium / 15** until rows are added.

| Rule | Code | Evidence |
|------|------|----------|
| Missing Secure | `COOKIE_MISSING_SECURE` | `Cookies missing Secure flag: {missing_secure_evidence}` |
| Missing HttpOnly | `COOKIE_MISSING_HTTPONLY` | `Cookies accessible by JavaScript: {missing_httponly_evidence}` |
| Missing SameSite | `COOKIE_MISSING_SAMESITE` | `Cookies missing SameSite attribute: {missing_samesite_evidence}` |
| Sensitive insecure | `COOKIE_SENSITIVE_INSECURE` | `Sensitive cookies missing Secure or HttpOnly: {sensitive_insecure_evidence}` |
| Long expiration | `COOKIE_LONG_EXPIRATION` | `Persistent cookies with long expiration: {long_expiration_evidence}` |
| Oversized | `COOKIE_OVERSIZED` | `Cookies exceed recommended 4KB size: {oversized_evidence}` |
| Duplicate names | `COOKIE_DUPLICATE` | `Duplicate cookie names detected: {duplicate_names_evidence}` |
| Too many cookies | `COOKIE_TOO_MANY` | `{cookie_count} Set-Cookie headers returned (recommended limit: 20)` |

---

## CVE (`cve`) — limited lookup, not a CVE product

| Rule | Code | Severity | Weight | Evidence |
|------|------|----------|--------:|----------|
| Known CVE Detected | `CVE_KNOWN_VULNERABILITY` | high | 40 | `{cve} affects installed package {name} {version}` (OSV hint path) |

---

## Monitoring (`monitoring`)

Host security findings (not CPU/disk alerts). Plugin id `monitoring`.

| Rule | Code | Severity | Weight | Evidence (typical) |
|------|------|----------|--------:|----------|
| SSH Password Authentication Enabled | `SSH_PASSWORD_AUTH` | medium | 15 | `PasswordAuthentication=yes` |
| SSH Root Login Enabled | `SSH_ROOT_LOGIN` | high | 30 | `PermitRootLogin=…` |
| SSH Public Key Authentication Disabled | `SSH_PUBKEY_DISABLED` | high | 30 | `PubkeyAuthentication=no` |
| SSH Protocol 1 Enabled | `SSH_PROTOCOL_LEGACY` | critical | 50 | `Protocol=1` |
| Firewall is not active | `FIREWALL_INACTIVE` | high | 30 | `backend=…` |
| Fail2Ban is not installed | `FAIL2BAN_NOT_INSTALLED` | medium | 15 | `fail2ban.installed=false` |
| Fail2Ban is not running | `FAIL2BAN_INACTIVE` | medium | 15 | `fail2ban.running=false` |
| Security updates pending | `SECURITY_UPDATES_PENDING` | medium | 15 | `security=N, available=M` |

**Disabled** (alerts only, migration `042`): `CPU_HIGH` (high/30), `RAM_HIGH` (high/30), `UPDATES_AVAILABLE` (low/5), `REBOOT_REQUIRED` (low/5). `SERVER_OFFLINE` is a monitoring **alert**, not a `risk_rules` row.

---

## Fingerprint

`evaluate_rules` returns **no** findings. No risk rules.

---

## Future stubs

`cloud` / `kubernetes` / `malware` catalogs or plugins exist with `enabled=False`. Do not treat those codes as V1 scored rules.

---

## How to refresh this page

When adding a scanner rule:

1. Add `RuleSpec` in `catalog_*.py` (match condition + evidence).
2. Seed `(plugin, finding_code, severity, score)` in an Alembic revision (`ON CONFLICT DO UPDATE`).
3. Add a row here with the **post-migration** severity and weight.
