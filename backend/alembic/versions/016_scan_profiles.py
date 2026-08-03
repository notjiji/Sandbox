"""Add custom scan profile and selected_plugins column

Revision ID: 016
Revises: 015
Create Date: 2026-08-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE scan_type ADD VALUE IF NOT EXISTS 'custom'")
    op.add_column(
        "scans",
        sa.Column("selected_plugins", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("scans", "selected_plugins")
    # PostgreSQL does not support removing enum values safely; leave scan_type as-is.
