"""WHOIS scanner risk rules

Revision ID: 032
Revises: 031
Create Date: 2026-08-07

"""
from typing import Sequence, Union

from alembic import op

revision: str = "032"
down_revision: Union[str, None] = "031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_WHOIS_RULES = """
INSERT INTO risk_rules (id, plugin, finding_code, title, description, severity, score, enabled)
VALUES
    (gen_random_uuid(), 'whois', 'WHOIS_EXPIRED', 'Domain Registration Expired', 'WHOIS expiration date is in the past.', 'critical', 45, true),
    (gen_random_uuid(), 'whois', 'WHOIS_EXPIRING_SOON', 'Domain Expiring Soon', 'WHOIS registration expires within 30 days.', 'low', 5, true),
    (gen_random_uuid(), 'whois', 'WHOIS_PRIVACY_DISABLED', 'WHOIS Privacy Disabled', 'Registrant contact details appear publicly visible.', 'low', 4, true),
    (gen_random_uuid(), 'whois', 'WHOIS_UNKNOWN_REGISTRAR', 'Unknown Domain Registrar', 'Registrar field missing or unknown.', 'medium', 8, true)
ON CONFLICT (plugin, finding_code) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    severity = EXCLUDED.severity,
    score = EXCLUDED.score,
    enabled = EXCLUDED.enabled,
    updated_at = now()
"""


def upgrade() -> None:
    op.execute(_WHOIS_RULES)


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM risk_rules
        WHERE plugin = 'whois'
          AND finding_code IN ('WHOIS_EXPIRED', 'WHOIS_PRIVACY_DISABLED', 'WHOIS_UNKNOWN_REGISTRAR')
        """
    )
