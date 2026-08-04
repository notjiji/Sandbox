"""Organization deleted_at and member removed status

Revision ID: 022
Revises: 021
Create Date: 2026-08-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "022"
down_revision: Union[str, None] = "021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("ALTER TYPE member_status ADD VALUE IF NOT EXISTS 'removed'")


def downgrade() -> None:
    op.drop_column("organizations", "deleted_at")
    # PostgreSQL enum values cannot be removed safely in downgrade.
