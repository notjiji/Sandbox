"""Scan lifecycle: queued status and per-transition timestamps

Revision ID: 017
Revises: 016
Create Date: 2026-08-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE scan_status ADD VALUE IF NOT EXISTS 'queued'")

    op.add_column("scans", sa.Column("pending_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("scans", sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("scans", sa.Column("running_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("scans", sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("scans", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))

    # Backfill lifecycle timestamps from existing rows.
    op.execute(
        """
        UPDATE scans
        SET pending_at = COALESCE(pending_at, created_at),
            running_at = COALESCE(running_at, started_at),
            completed_at = CASE
                WHEN status = 'completed' THEN COALESCE(completed_at, updated_at)
                ELSE completed_at
            END,
            failed_at = CASE
                WHEN status = 'failed' THEN COALESCE(failed_at, completed_at, updated_at)
                ELSE failed_at
            END,
            cancelled_at = CASE
                WHEN status = 'cancelled' THEN COALESCE(cancelled_at, completed_at, updated_at)
                ELSE cancelled_at
            END
        """
    )

    op.drop_column("scans", "started_at")


def downgrade() -> None:
    op.add_column("scans", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE scans SET started_at = running_at")
    op.drop_column("scans", "cancelled_at")
    op.drop_column("scans", "failed_at")
    op.drop_column("scans", "running_at")
    op.drop_column("scans", "queued_at")
    op.drop_column("scans", "pending_at")
    # PostgreSQL does not support removing enum values safely; leave scan_status as-is.
