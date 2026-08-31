"""Asset hierarchy and digital asset types

Revision ID: 011
Revises: 010
Create Date: 2026-07-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_enum_value(enum_name: str, value: str) -> None:
    op.execute(
        f"""
        DO $$ BEGIN
            ALTER TYPE {enum_name} ADD VALUE '{value}';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    )


def upgrade() -> None:
    # PostgreSQL requires new enum values to be committed before use in the same migration run.
    with op.get_context().autocommit_block():
        _add_enum_value("asset_type", "website")
        _add_enum_value("asset_type", "server")
        _add_enum_value("asset_type", "public_ip")

    op.add_column("assets", sa.Column("parent_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_assets_parent_id"), "assets", ["parent_id"], unique=False)
    op.create_foreign_key(
        "fk_assets_parent_id_assets",
        "assets",
        "assets",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.execute("UPDATE assets SET type = 'server' WHERE type = 'host'")
    op.execute("UPDATE assets SET type = 'website' WHERE type = 'application'")
    op.execute("UPDATE assets SET type = 'public_ip' WHERE type = 'ip'")


def downgrade() -> None:
    op.execute("UPDATE assets SET type = 'host' WHERE type = 'server'")
    op.execute("UPDATE assets SET type = 'application' WHERE type = 'website'")
    op.execute("UPDATE assets SET type = 'ip' WHERE type = 'public_ip'")

    op.drop_constraint("fk_assets_parent_id_assets", "assets", type_="foreignkey")
    op.drop_index(op.f("ix_assets_parent_id"), table_name="assets")
    op.drop_column("assets", "parent_id")
