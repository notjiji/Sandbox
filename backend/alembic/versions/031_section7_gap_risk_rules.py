"""Section 7 gap risk rules — DNSSEC, CT, CSP, ports, CVE

Revision ID: 031
Revises: 030
Create Date: 2026-08-07

"""
from typing import Sequence, Union

from alembic import op

revision: str = "031"
down_revision: Union[str, None] = "030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SECTION7_RULES = """
INSERT INTO risk_rules (id, plugin, finding_code, title, description, severity, score, enabled)
VALUES
    (gen_random_uuid(), 'dns', 'DNS_DNSSEC_INVALID', 'DNSSEC Validation Failed', 'DNSSEC chain failed validation.', 'high', 28, true),
    (gen_random_uuid(), 'ssl', 'SSL_CT_SUSPICIOUS_ISSUER', 'Suspicious CT Issuer', 'Certificate Transparency log contains unexpected issuers.', 'medium', 15, true),
    (gen_random_uuid(), 'http_headers', 'HTTP_CSP_BROAD_SOURCES', 'Overly Broad CSP Sources', 'CSP allows data:, blob:, or scheme-wide https: sources.', 'medium', 12, true),
    (gen_random_uuid(), 'ports', 'PORT_FTP_OPEN', 'FTP Port Open', 'FTP service detected on an open port.', 'medium', 18, true),
    (gen_random_uuid(), 'ports', 'PORT_SMB_OPEN', 'SMB Port Open', 'SMB service detected on an open port.', 'high', 30, true),
    (gen_random_uuid(), 'ports', 'PORT_RDP_OPEN', 'RDP Port Open', 'Remote Desktop port is exposed.', 'high', 35, true),
    (gen_random_uuid(), 'cve', 'CVE_KNOWN_VULNERABILITY', 'Known CVE Detected', 'Installed software matched a published CVE via OSV.', 'high', 40, true)
ON CONFLICT (plugin, finding_code) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    severity = EXCLUDED.severity,
    score = EXCLUDED.score,
    enabled = EXCLUDED.enabled,
    updated_at = now()
"""


def upgrade() -> None:
    op.execute(_SECTION7_RULES)


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM risk_rules
        WHERE finding_code IN (
            'DNS_DNSSEC_INVALID', 'SSL_CT_SUSPICIOUS_ISSUER', 'HTTP_CSP_BROAD_SOURCES',
            'PORT_FTP_OPEN', 'PORT_SMB_OPEN', 'PORT_RDP_OPEN', 'CVE_KNOWN_VULNERABILITY'
        )
        """
    )
