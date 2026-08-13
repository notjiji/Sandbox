"""Disable operational conditions from monitoring risk rules.

Alerts (CPU, RAM, reboot, generic updates) are not findings.

Revision ID: 042
Revises: 041_findings_monitoring_source
Create Date: 2026-08-13
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "042_alerts_vs_findings"
down_revision: Union[str, None] = "041_findings_monitoring_source"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ALERT_ONLY_CODES = ("CPU_HIGH", "RAM_HIGH", "UPDATES_AVAILABLE", "REBOOT_REQUIRED")


def upgrade() -> None:
    conn = op.get_bind()
    for finding_code in _ALERT_ONLY_CODES:
        conn.execute(
            sa.text(
                """
                UPDATE risk_rules
                SET enabled = false, updated_at = now()
                WHERE plugin = 'monitoring' AND finding_code = :finding_code
                """
            ),
            {"finding_code": finding_code},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for finding_code in _ALERT_ONLY_CODES:
        conn.execute(
            sa.text(
                """
                UPDATE risk_rules
                SET enabled = true, updated_at = now()
                WHERE plugin = 'monitoring' AND finding_code = :finding_code
                """
            ),
            {"finding_code": finding_code},
        )
