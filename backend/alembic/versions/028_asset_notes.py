"""Asset notes — migration 028

Revision ID: 028
Revises: 027
Create Date: 2026-08-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "028"
down_revision: Union[str, None] = "027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("assets", sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("assets", "notes")
