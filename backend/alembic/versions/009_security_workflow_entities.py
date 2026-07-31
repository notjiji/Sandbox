"""assets, scans, findings, reports — project-scoped security workflow

Revision ID: 009
Revises: 008
Create Date: 2026-07-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

asset_type = postgresql.ENUM("host", "domain", "ip", "application", name="asset_type", create_type=False)
asset_status = postgresql.ENUM("active", "inactive", "archived", name="asset_status", create_type=False)
scan_status = postgresql.ENUM(
    "pending", "running", "completed", "failed", "cancelled", name="scan_status", create_type=False
)
scan_type = postgresql.ENUM("full", "quick", name="scan_type", create_type=False)
finding_severity = postgresql.ENUM(
    "critical", "high", "medium", "low", "info", name="finding_severity", create_type=False
)
finding_status = postgresql.ENUM(
    "open", "in_review", "resolved", "false_positive", "accepted", name="finding_status", create_type=False
)
report_status = postgresql.ENUM("draft", "generating", "ready", "failed", name="report_status", create_type=False)


def upgrade() -> None:
    for enum_type in (
        asset_type,
        asset_status,
        scan_status,
        scan_type,
        finding_severity,
        finding_status,
        report_status,
    ):
        enum_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "assets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("identifier", sa.String(length=512), nullable=True),
        sa.Column("type", asset_type, nullable=False, server_default="host"),
        sa.Column("status", asset_status, nullable=False, server_default="active"),
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
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assets_project_id"), "assets", ["project_id"], unique=False)

    op.create_table(
        "scans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("asset_id", sa.UUID(), nullable=False),
        sa.Column("scan_type", scan_type, nullable=False, server_default="full"),
        sa.Column("status", scan_status, nullable=False, server_default="pending"),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scans_project_id"), "scans", ["project_id"], unique=False)
    op.create_index(op.f("ix_scans_asset_id"), "scans", ["asset_id"], unique=False)

    op.create_table(
        "findings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("scan_id", sa.UUID(), nullable=False),
        sa.Column("asset_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", finding_severity, nullable=False, server_default="medium"),
        sa.Column("status", finding_status, nullable=False, server_default="open"),
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
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_findings_project_id"), "findings", ["project_id"], unique=False)
    op.create_index(op.f("ix_findings_scan_id"), "findings", ["scan_id"], unique=False)
    op.create_index(op.f("ix_findings_asset_id"), "findings", ["asset_id"], unique=False)

    op.create_table(
        "reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", report_status, nullable=False, server_default="draft"),
        sa.Column("file_url", sa.String(length=1024), nullable=True),
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
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_project_id"), "reports", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reports_project_id"), table_name="reports")
    op.drop_table("reports")

    op.drop_index(op.f("ix_findings_asset_id"), table_name="findings")
    op.drop_index(op.f("ix_findings_scan_id"), table_name="findings")
    op.drop_index(op.f("ix_findings_project_id"), table_name="findings")
    op.drop_table("findings")

    op.drop_index(op.f("ix_scans_asset_id"), table_name="scans")
    op.drop_index(op.f("ix_scans_project_id"), table_name="scans")
    op.drop_table("scans")

    op.drop_index(op.f("ix_assets_project_id"), table_name="assets")
    op.drop_table("assets")

    for enum_type in reversed(
        [report_status, finding_status, finding_severity, scan_type, scan_status, asset_status, asset_type]
    ):
        enum_type.drop(op.get_bind(), checkfirst=True)
