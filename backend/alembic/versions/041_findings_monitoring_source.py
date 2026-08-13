"""Findings source field and monitoring risk rules.

Revision ID: 041
Revises: 040_monitoring_metrics
Create Date: 2026-08-13
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "041_findings_monitoring_source"
down_revision: Union[str, None] = "040_monitoring_metrics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_MONITORING_RULES = [
    ("SSH_PASSWORD_AUTH", "SSH Password Authentication Enabled", "Password authentication allows brute-force login attempts.", "medium", 15),
    ("SSH_ROOT_LOGIN", "SSH Root Login Enabled", "Direct root SSH login increases blast radius on compromise.", "high", 30),
    ("SSH_PUBKEY_DISABLED", "SSH Public Key Authentication Disabled", "Hosts cannot use key-based SSH login.", "high", 30),
    ("SSH_PROTOCOL_LEGACY", "SSH Protocol 1 Enabled", "SSH protocol 1 is obsolete and insecure.", "critical", 50),
    ("FIREWALL_INACTIVE", "Firewall is not active", "Host firewall reported as disabled.", "high", 30),
    ("FAIL2BAN_NOT_INSTALLED", "Fail2Ban is not installed", "No intrusion prevention service is installed.", "medium", 15),
    ("FAIL2BAN_INACTIVE", "Fail2Ban is not running", "Fail2Ban is installed but inactive.", "medium", 15),
    ("SECURITY_UPDATES_PENDING", "Security updates pending", "Unapplied security patches increase exposure.", "medium", 15),
    ("CPU_HIGH", "High CPU usage", "Sustained high CPU may indicate overload or runaway processes.", "high", 30),
    ("RAM_HIGH", "High memory usage", "Sustained high memory may lead to OOM instability.", "high", 30),
    ("UPDATES_AVAILABLE", "System updates available", "Non-security updates are pending.", "low", 5),
    ("REBOOT_REQUIRED", "System reboot required", "Kernel or library updates require a reboot.", "low", 5),
]


def upgrade() -> None:
    op.add_column(
        "findings",
        sa.Column("source", sa.String(length=32), nullable=False, server_default="scan"),
    )
    op.create_index("ix_findings_source", "findings", ["source"])
    op.alter_column("findings", "scan_id", existing_type=sa.UUID(), nullable=True)

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_findings_monitoring_asset_code
        ON findings (asset_id, finding_code)
        WHERE source = 'monitoring' AND finding_code IS NOT NULL
        """
    )

    conn = op.get_bind()
    for finding_code, title, description, severity, score in _MONITORING_RULES:
        conn.execute(
            sa.text(
                """
                INSERT INTO risk_rules (id, plugin, finding_code, title, description, severity, score, enabled, created_at, updated_at)
                VALUES (gen_random_uuid(), 'monitoring', :finding_code, :title, :description, :severity, :score, true, now(), now())
                ON CONFLICT (plugin, finding_code) DO NOTHING
                """
            ),
            {
                "finding_code": finding_code,
                "title": title,
                "description": description,
                "severity": severity,
                "score": score,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    for finding_code, *_rest in _MONITORING_RULES:
        conn.execute(
            sa.text("DELETE FROM risk_rules WHERE plugin = 'monitoring' AND finding_code = :finding_code"),
            {"finding_code": finding_code},
        )

    op.execute("DROP INDEX IF EXISTS uq_findings_monitoring_asset_code")
    op.alter_column("findings", "scan_id", existing_type=sa.UUID(), nullable=False)
    op.drop_index("ix_findings_source", table_name="findings")
    op.drop_column("findings", "source")
