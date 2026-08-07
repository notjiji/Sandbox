"""Port scanner risk rules v3

Revision ID: 033
Revises: 032
Create Date: 2026-08-07

"""
from typing import Sequence, Union

from alembic import op

revision: str = "033"
down_revision: Union[str, None] = "032"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PORT_RULES = """
INSERT INTO risk_rules (id, plugin, finding_code, title, description, severity, score, enabled)
VALUES
    (gen_random_uuid(), 'ports', 'PORT_FTP_OPEN', 'FTP Port Open', 'FTP service detected on a public port.', 'medium', 18, true),
    (gen_random_uuid(), 'ports', 'PORT_TELNET_OPEN', 'Telnet Port Open', 'Telnet service detected on an open port.', 'critical', 45, true),
    (gen_random_uuid(), 'ports', 'PORT_RDP_EXPOSED', 'RDP Exposed', 'Remote Desktop port is publicly reachable.', 'high', 35, true),
    (gen_random_uuid(), 'ports', 'PORT_MYSQL_PUBLIC', 'MySQL Publicly Exposed', 'MySQL port is reachable from the scan vantage.', 'high', 32, true),
    (gen_random_uuid(), 'ports', 'PORT_REDIS_PUBLIC', 'Redis Publicly Exposed', 'Redis port is reachable from the scan vantage.', 'high', 34, true),
    (gen_random_uuid(), 'ports', 'PORT_MONGODB_PUBLIC', 'MongoDB Publicly Exposed', 'MongoDB port is reachable from the scan vantage.', 'high', 36, true)
ON CONFLICT (plugin, finding_code) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    severity = EXCLUDED.severity,
    score = EXCLUDED.score,
    enabled = EXCLUDED.enabled,
    updated_at = now()
"""


def upgrade() -> None:
    op.execute(_PORT_RULES)
    op.execute(
        """
        UPDATE risk_rules
        SET enabled = false, updated_at = now()
        WHERE plugin = 'ports' AND finding_code = 'PORT_RDP_OPEN'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM risk_rules
        WHERE plugin = 'ports'
          AND finding_code IN ('PORT_RDP_EXPOSED', 'PORT_MYSQL_PUBLIC', 'PORT_REDIS_PUBLIC', 'PORT_MONGODB_PUBLIC')
        """
    )
    op.execute(
        """
        UPDATE risk_rules
        SET enabled = true, updated_at = now()
        WHERE plugin = 'ports' AND finding_code = 'PORT_RDP_OPEN'
        """
    )
