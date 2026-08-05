"""Asset-scoped reports — type, asset link, pagination

Revision ID: 025
Revises: 024
Create Date: 2026-08-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM

revision: str = "025"
down_revision: Union[str, None] = "024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

report_type_enum = ENUM(
    "executive",
    "technical",
    "weekly",
    "monthly",
    name="report_type",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        "CREATE TYPE report_type AS ENUM ('executive', 'technical', 'weekly', 'monthly')"
    )
    op.add_column(
        "reports",
        sa.Column("asset_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "reports",
        sa.Column(
            "report_type",
            report_type_enum,
            nullable=False,
            server_default="executive",
        ),
    )
    op.create_foreign_key(
        "fk_reports_asset_id",
        "reports",
        "assets",
        ["asset_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f("ix_reports_asset_id"), "reports", ["asset_id"], unique=False)
    op.alter_column("reports", "report_type", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_reports_asset_id"), table_name="reports")
    op.drop_constraint("fk_reports_asset_id", "reports", type_="foreignkey")
    op.drop_column("reports", "report_type")
    op.drop_column("reports", "asset_id")
    op.execute("DROP TYPE report_type")
