"""Monitoring agents, snapshots, and security alerts.

Revision ID: 039
Revises: 038
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "039_monitoring_agent"
down_revision: Union[str, None] = "038_report_pipeline_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

agent_status = postgresql.ENUM(
    "pending",
    "online",
    "offline",
    "revoked",
    name="agent_status",
    create_type=False,
)
monitoring_alert_severity = postgresql.ENUM(
    "critical",
    "high",
    "medium",
    "low",
    "info",
    name="monitoring_alert_severity",
    create_type=False,
)
monitoring_alert_status = postgresql.ENUM(
    "open",
    "resolved",
    name="monitoring_alert_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    agent_status.create(bind, checkfirst=True)
    monitoring_alert_severity.create(bind, checkfirst=True)
    monitoring_alert_status.create(bind, checkfirst=True)

    op.create_table(
        "monitoring_agents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("asset_id", sa.UUID(), nullable=False),
        sa.Column("enrollment_token_hash", sa.String(length=64), nullable=True),
        sa.Column("enrollment_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("credential_hash", sa.String(length=64), nullable=True),
        sa.Column("status", agent_status, nullable=False, server_default="pending"),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("agent_version", sa.String(length=32), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", name="uq_monitoring_agents_asset_id"),
    )
    op.create_index("ix_monitoring_agents_organization_id", "monitoring_agents", ["organization_id"])
    op.create_index("ix_monitoring_agents_project_id", "monitoring_agents", ["project_id"])
    op.create_index("ix_monitoring_agents_asset_id", "monitoring_agents", ["asset_id"])
    op.create_index(
        "ix_monitoring_agents_enrollment_token_hash",
        "monitoring_agents",
        ["enrollment_token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_monitoring_agents_credential_hash",
        "monitoring_agents",
        ["credential_hash"],
        unique=True,
    )

    op.create_table(
        "monitoring_snapshots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("asset_id", sa.UUID(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cpu_percent", sa.Float(), nullable=True),
        sa.Column("ram_percent", sa.Float(), nullable=True),
        sa.Column("ram_used_mb", sa.Float(), nullable=True),
        sa.Column("ram_total_mb", sa.Float(), nullable=True),
        sa.Column("disk_percent", sa.Float(), nullable=True),
        sa.Column("disk_used_gb", sa.Float(), nullable=True),
        sa.Column("disk_total_gb", sa.Float(), nullable=True),
        sa.Column("uptime_seconds", sa.Integer(), nullable=True),
        sa.Column("load_avg_1", sa.Float(), nullable=True),
        sa.Column("process_count", sa.Integer(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["monitoring_agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitoring_snapshots_agent_id", "monitoring_snapshots", ["agent_id"])
    op.create_index("ix_monitoring_snapshots_asset_id", "monitoring_snapshots", ["asset_id"])
    op.create_index("ix_monitoring_snapshots_collected_at", "monitoring_snapshots", ["collected_at"])

    op.create_table(
        "monitoring_alerts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("asset_id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("alert_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("severity", monitoring_alert_severity, nullable=False, server_default="medium"),
        sa.Column("status", monitoring_alert_status, nullable=False, server_default="open"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["monitoring_agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", "alert_code", name="uq_monitoring_alerts_asset_code"),
    )
    op.create_index("ix_monitoring_alerts_organization_id", "monitoring_alerts", ["organization_id"])
    op.create_index("ix_monitoring_alerts_project_id", "monitoring_alerts", ["project_id"])
    op.create_index("ix_monitoring_alerts_asset_id", "monitoring_alerts", ["asset_id"])
    op.create_index("ix_monitoring_alerts_agent_id", "monitoring_alerts", ["agent_id"])
    op.create_index("ix_monitoring_alerts_alert_code", "monitoring_alerts", ["alert_code"])
    op.create_index("ix_monitoring_alerts_status", "monitoring_alerts", ["status"])


def downgrade() -> None:
    op.drop_index("ix_monitoring_alerts_status", table_name="monitoring_alerts")
    op.drop_index("ix_monitoring_alerts_alert_code", table_name="monitoring_alerts")
    op.drop_index("ix_monitoring_alerts_agent_id", table_name="monitoring_alerts")
    op.drop_index("ix_monitoring_alerts_asset_id", table_name="monitoring_alerts")
    op.drop_index("ix_monitoring_alerts_project_id", table_name="monitoring_alerts")
    op.drop_index("ix_monitoring_alerts_organization_id", table_name="monitoring_alerts")
    op.drop_table("monitoring_alerts")

    op.drop_index("ix_monitoring_snapshots_collected_at", table_name="monitoring_snapshots")
    op.drop_index("ix_monitoring_snapshots_asset_id", table_name="monitoring_snapshots")
    op.drop_index("ix_monitoring_snapshots_agent_id", table_name="monitoring_snapshots")
    op.drop_table("monitoring_snapshots")

    op.drop_index("ix_monitoring_agents_credential_hash", table_name="monitoring_agents")
    op.drop_index("ix_monitoring_agents_enrollment_token_hash", table_name="monitoring_agents")
    op.drop_index("ix_monitoring_agents_asset_id", table_name="monitoring_agents")
    op.drop_index("ix_monitoring_agents_project_id", table_name="monitoring_agents")
    op.drop_index("ix_monitoring_agents_organization_id", table_name="monitoring_agents")
    op.drop_table("monitoring_agents")

    bind = op.get_bind()
    monitoring_alert_status.drop(bind, checkfirst=True)
    monitoring_alert_severity.drop(bind, checkfirst=True)
    agent_status.drop(bind, checkfirst=True)
