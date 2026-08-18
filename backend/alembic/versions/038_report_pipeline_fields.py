"""Report pipeline fields: scan binding, file metadata, version."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "038_report_pipeline_fields"
down_revision = "037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("scan_id", sa.UUID(), nullable=True))
    op.add_column("reports", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("reports", sa.Column("file_size", sa.BigInteger(), nullable=True))
    op.add_column(
        "reports",
        sa.Column("report_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_foreign_key(
        "fk_reports_scan_id_scans",
        "reports",
        "scans",
        ["scan_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_reports_scan_id", "reports", ["scan_id"])


def downgrade() -> None:
    op.drop_index("ix_reports_scan_id", table_name="reports")
    op.drop_constraint("fk_reports_scan_id_scans", "reports", type_="foreignkey")
    op.drop_column("reports", "report_version")
    op.drop_column("reports", "file_size")
    op.drop_column("reports", "completed_at")
    op.drop_column("reports", "scan_id")
