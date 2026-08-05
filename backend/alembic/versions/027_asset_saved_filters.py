"""Asset saved filters — migration 027

Revision ID: 027
Revises: 026
Create Date: 2026-08-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "027"
down_revision: Union[str, None] = "026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "asset_saved_filters",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("filters_json", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "user_id",
            "name",
            name="uq_asset_saved_filters_project_user_name",
        ),
    )
    op.create_index(
        op.f("ix_asset_saved_filters_organization_id"),
        "asset_saved_filters",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_asset_saved_filters_project_id"),
        "asset_saved_filters",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_asset_saved_filters_user_id"),
        "asset_saved_filters",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_asset_saved_filters_user_id"), table_name="asset_saved_filters")
    op.drop_index(op.f("ix_asset_saved_filters_project_id"), table_name="asset_saved_filters")
    op.drop_index(
        op.f("ix_asset_saved_filters_organization_id"),
        table_name="asset_saved_filters",
    )
    op.drop_table("asset_saved_filters")
