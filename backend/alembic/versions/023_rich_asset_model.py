"""Rich asset model — classification and lifecycle fields

Revision ID: 023
Revises: 022
Create Date: 2026-08-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM

revision: str = "023"
down_revision: Union[str, None] = "022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

asset_category_enum = ENUM(
    "infrastructure",
    "application",
    "data",
    "network",
    "identity",
    "endpoint",
    "cloud",
    "other",
    name="asset_category",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        "CREATE TYPE asset_category AS ENUM ("
        "'infrastructure', 'application', 'data', 'network', "
        "'identity', 'endpoint', 'cloud', 'other'"
        ")"
    )
    op.add_column("assets", sa.Column("external_identifier", sa.String(length=512), nullable=True))
    op.add_column("assets", sa.Column("business_unit", sa.String(length=128), nullable=True))
    op.add_column(
        "assets",
        sa.Column("asset_category", asset_category_enum, nullable=True),
    )
    op.add_column("assets", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("assets", sa.Column("archived_by", sa.UUID(), nullable=True))
    op.add_column("assets", sa.Column("updated_by", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_assets_archived_by_users",
        "assets",
        "users",
        ["archived_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_assets_updated_by_users",
        "assets",
        "users",
        ["updated_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_assets_updated_by_users", "assets", type_="foreignkey")
    op.drop_constraint("fk_assets_archived_by_users", "assets", type_="foreignkey")
    op.drop_column("assets", "updated_by")
    op.drop_column("assets", "archived_by")
    op.drop_column("assets", "archived_at")
    op.drop_column("assets", "asset_category")
    op.drop_column("assets", "business_unit")
    op.drop_column("assets", "external_identifier")
    op.execute("DROP TYPE IF EXISTS asset_category")
