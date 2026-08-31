"""Per-asset scan schedules — migration 026

Revision ID: 026
Revises: 025
Create Date: 2026-08-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM

revision: str = "026"
down_revision: Union[str, None] = "025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

schedule_preset_enum = ENUM(
    "quick_daily",
    "full_sunday",
    "ssl_12h",
    "dns_weekly",
    name="schedule_preset",
    create_type=False,
)
scan_type_enum = ENUM(
    "quick",
    "full",
    "custom",
    name="scan_type",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        "CREATE TYPE schedule_preset AS ENUM "
        "('quick_daily', 'full_sunday', 'ssl_12h', 'dns_weekly')"
    )
    op.create_table(
        "asset_scan_schedules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("asset_id", sa.UUID(), nullable=False),
        sa.Column("preset", schedule_preset_enum, nullable=False),
        sa.Column(
            "scan_type",
            scan_type_enum,
            nullable=False,
        ),
        sa.Column("selected_plugins", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_scan_id", sa.UUID(), nullable=True),
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
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["last_scan_id"], ["scans.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", "preset", name="uq_asset_scan_schedules_asset_preset"),
    )
    op.create_index(
        op.f("ix_asset_scan_schedules_asset_id"),
        "asset_scan_schedules",
        ["asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_asset_scan_schedules_project_id"),
        "asset_scan_schedules",
        ["project_id"],
        unique=False,
    )
    op.alter_column("asset_scan_schedules", "enabled", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_asset_scan_schedules_project_id"), table_name="asset_scan_schedules")
    op.drop_index(op.f("ix_asset_scan_schedules_asset_id"), table_name="asset_scan_schedules")
    op.drop_table("asset_scan_schedules")
    op.execute("DROP TYPE schedule_preset")
