"""Asset links — peer relationships beyond parent/child hierarchy

Revision ID: 024
Revises: 023
Create Date: 2026-08-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM

revision: str = "024"
down_revision: Union[str, None] = "023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

asset_link_type_enum = ENUM(
    "depends_on",
    "hosts",
    "runs_on",
    "exposes",
    "related",
    name="asset_link_type",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        "CREATE TYPE asset_link_type AS ENUM ("
        "'depends_on', 'hosts', 'runs_on', 'exposes', 'related'"
        ")"
    )
    op.create_table(
        "asset_links",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("source_asset_id", sa.UUID(), nullable=False),
        sa.Column("target_asset_id", sa.UUID(), nullable=False),
        sa.Column("link_type", asset_link_type_enum, nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_asset_id",
            "target_asset_id",
            "link_type",
            name="uq_asset_links_source_target_type",
        ),
    )
    op.create_index("ix_asset_links_organization_id", "asset_links", ["organization_id"])
    op.create_index("ix_asset_links_source_asset_id", "asset_links", ["source_asset_id"])
    op.create_index("ix_asset_links_target_asset_id", "asset_links", ["target_asset_id"])


def downgrade() -> None:
    op.drop_index("ix_asset_links_target_asset_id", table_name="asset_links")
    op.drop_index("ix_asset_links_source_asset_id", table_name="asset_links")
    op.drop_index("ix_asset_links_organization_id", table_name="asset_links")
    op.drop_table("asset_links")
    op.execute("DROP TYPE IF EXISTS asset_link_type")
