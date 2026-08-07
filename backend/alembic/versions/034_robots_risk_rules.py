"""Robots.txt scanner risk rules v2

Revision ID: 034
Revises: 033
Create Date: 2026-08-07

"""
from typing import Sequence, Union

from alembic import op

revision: str = "034"
down_revision: Union[str, None] = "033"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ROBOTS_RULES = """
INSERT INTO risk_rules (id, plugin, finding_code, title, description, severity, score, enabled)
VALUES
    (gen_random_uuid(), 'robots', 'ROBOTS_ADMIN_PATH_DISCLOSED', 'Admin Paths Disclosed in robots.txt', 'Admin-related paths are referenced in the public robots.txt file.', 'medium', 12, true),
    (gen_random_uuid(), 'robots', 'ROBOTS_DEBUG_PATH_DISCLOSED', 'Debug Paths Disclosed in robots.txt', 'Debug or test paths are referenced in the public robots.txt file.', 'high', 22, true),
    (gen_random_uuid(), 'robots', 'ROBOTS_SENSITIVE_PATH_DISCLOSED', 'Sensitive Paths Disclosed in robots.txt', 'Internal, backup, or configuration paths are referenced in robots.txt.', 'low', 6, true)
ON CONFLICT (plugin, finding_code) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    severity = EXCLUDED.severity,
    score = EXCLUDED.score,
    enabled = EXCLUDED.enabled,
    updated_at = now()
"""


def upgrade() -> None:
    op.execute(_ROBOTS_RULES)


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM risk_rules
        WHERE plugin = 'robots'
          AND finding_code IN (
            'ROBOTS_ADMIN_PATH_DISCLOSED',
            'ROBOTS_DEBUG_PATH_DISCLOSED',
            'ROBOTS_SENSITIVE_PATH_DISCLOSED'
          )
        """
    )
