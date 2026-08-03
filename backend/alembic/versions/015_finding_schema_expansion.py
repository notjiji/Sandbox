"""Finding schema expansion + plugin run duration

Revision ID: 015
Revises: 014
Create Date: 2026-08-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("findings", sa.Column("plugin", sa.String(length=128), nullable=True))
    op.add_column("findings", sa.Column("evidence", sa.Text(), nullable=True))
    op.add_column("findings", sa.Column("recommendation", sa.Text(), nullable=True))
    op.add_column("findings", sa.Column("references", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("findings", sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("findings", sa.Column("confidence", sa.Float(), nullable=True))
    op.add_column("findings", sa.Column("detected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("scan_plugin_runs", sa.Column("duration_seconds", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("scan_plugin_runs", "duration_seconds")
    op.drop_column("findings", "detected_at")
    op.drop_column("findings", "confidence")
    op.drop_column("findings", "raw_data")
    op.drop_column("findings", "references")
    op.drop_column("findings", "recommendation")
    op.drop_column("findings", "evidence")
    op.drop_column("findings", "plugin")
