"""security.txt scanner risk rules

Revision ID: 035
Revises: 034
Create Date: 2026-08-07

"""
from typing import Sequence, Union

from alembic import op

revision: str = "035"
down_revision: Union[str, None] = "034"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SECURITY_TXT_RULES = """
INSERT INTO risk_rules (id, plugin, finding_code, title, description, severity, score, enabled)
VALUES
    (gen_random_uuid(), 'security_txt', 'SECURITY_TXT_MISSING', 'Missing security.txt', 'No valid /.well-known/security.txt was found.', 'low', 3, true),
    (gen_random_uuid(), 'security_txt', 'SECURITY_TXT_MISSING_CONTACT', 'security.txt Missing Contact', 'security.txt is present but does not define a Contact field.', 'medium', 10, true),
    (gen_random_uuid(), 'security_txt', 'SECURITY_TXT_INVALID_CONTACT', 'security.txt Invalid Contact', 'One or more Contact values are invalid.', 'medium', 10, true),
    (gen_random_uuid(), 'security_txt', 'SECURITY_TXT_EXPIRED', 'security.txt Expired', 'The Expires field is in the past.', 'medium', 12, true),
    (gen_random_uuid(), 'security_txt', 'SECURITY_TXT_MISSING_EXPIRES', 'security.txt Missing Expires', 'security.txt does not define an Expires field.', 'low', 4, true),
    (gen_random_uuid(), 'security_txt', 'SECURITY_TXT_INVALID_ENCRYPTION', 'security.txt Invalid Encryption', 'One or more Encryption URIs are invalid.', 'low', 4, true),
    (gen_random_uuid(), 'security_txt', 'SECURITY_TXT_INVALID_CANONICAL', 'security.txt Invalid Canonical', 'Canonical URI is invalid or mismatched.', 'low', 4, true)
ON CONFLICT (plugin, finding_code) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    severity = EXCLUDED.severity,
    score = EXCLUDED.score,
    enabled = EXCLUDED.enabled,
    updated_at = now()
"""


def upgrade() -> None:
    op.execute(_SECURITY_TXT_RULES)
    op.execute(
        """
        UPDATE risk_rules
        SET enabled = false, updated_at = now()
        WHERE plugin = 'http_headers' AND finding_code = 'HTTP_MISSING_SECURITY_TXT'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM risk_rules
        WHERE plugin = 'security_txt'
          AND finding_code IN (
            'SECURITY_TXT_MISSING',
            'SECURITY_TXT_MISSING_CONTACT',
            'SECURITY_TXT_INVALID_CONTACT',
            'SECURITY_TXT_EXPIRED',
            'SECURITY_TXT_MISSING_EXPIRES',
            'SECURITY_TXT_INVALID_ENCRYPTION',
            'SECURITY_TXT_INVALID_CANONICAL'
          )
        """
    )
    op.execute(
        """
        UPDATE risk_rules
        SET enabled = true, updated_at = now()
        WHERE plugin = 'http_headers' AND finding_code = 'HTTP_MISSING_SECURITY_TXT'
        """
    )
