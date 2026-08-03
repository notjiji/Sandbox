"""Scan plugin runs — per-plugin execution status

Revision ID: 014
Revises: 013
Create Date: 2026-08-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

plugin_run_status = postgresql.ENUM(
    "pending",
    "running",
    "completed",
    "failed",
    "skipped",
    name="plugin_run_status",
    create_type=False,
)


def upgrade() -> None:
    plugin_run_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "scan_plugin_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("scan_id", sa.UUID(), nullable=False),
        sa.Column("asset_id", sa.UUID(), nullable=False),
        sa.Column("plugin_name", sa.String(length=128), nullable=False),
        sa.Column("status", plugin_run_status, nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("findings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_id", "asset_id", "plugin_name", name="uq_scan_plugin_runs_scan_asset_plugin"),
    )
    op.create_index(op.f("ix_scan_plugin_runs_scan_id"), "scan_plugin_runs", ["scan_id"], unique=False)
    op.create_index(op.f("ix_scan_plugin_runs_asset_id"), "scan_plugin_runs", ["asset_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_scan_plugin_runs_asset_id"), table_name="scan_plugin_runs")
    op.drop_index(op.f("ix_scan_plugin_runs_scan_id"), table_name="scan_plugin_runs")
    op.drop_table("scan_plugin_runs")
    plugin_run_status.drop(op.get_bind(), checkfirst=True)
