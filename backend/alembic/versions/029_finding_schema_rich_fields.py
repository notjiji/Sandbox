"""Finding schema expansion — migration 029

Revision ID: 029
Revises: 028
Create Date: 2026-08-06

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "029"
down_revision: Union[str, None] = "028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("findings", sa.Column("category", sa.String(length=128), nullable=True))
    op.add_column("findings", sa.Column("cwe", sa.String(length=32), nullable=True))
    op.add_column("findings", sa.Column("cve", sa.String(length=32), nullable=True))
    op.add_column("findings", sa.Column("cvss", sa.Float(), nullable=True))
    op.add_column("findings", sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("findings", "resolved_at")
    op.drop_column("findings", "cvss")
    op.drop_column("findings", "cve")
    op.drop_column("findings", "cwe")
    op.drop_column("findings", "category")
