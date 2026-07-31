"""organization profile fields, member lifecycle, project created_by

Revision ID: 008
Revises: 007
Create Date: 2026-07-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

member_status = postgresql.ENUM(
    "invited",
    "active",
    "suspended",
    name="member_status",
    create_type=False,
)


def upgrade() -> None:
    member_status.create(op.get_bind(), checkfirst=True)

    op.add_column("organizations", sa.Column("industry", sa.String(length=128), nullable=True))
    op.add_column("organizations", sa.Column("website", sa.String(length=512), nullable=True))
    op.add_column("organizations", sa.Column("logo_url", sa.String(length=1024), nullable=True))
    op.add_column("organizations", sa.Column("country", sa.String(length=2), nullable=True))
    op.add_column("organizations", sa.Column("timezone", sa.String(length=64), nullable=True))
    op.add_column("organizations", sa.Column("created_by", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_organizations_created_by_users",
        "organizations",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "organization_members",
        sa.Column(
            "status",
            member_status,
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column(
        "organization_members",
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE organization_members SET joined_at = created_at WHERE status = 'active'"
        )
    )

    op.add_column("projects", sa.Column("created_by", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_projects_created_by_users",
        "projects",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_projects_created_by_users", "projects", type_="foreignkey")
    op.drop_column("projects", "created_by")

    op.drop_column("organization_members", "joined_at")
    op.drop_column("organization_members", "status")
    member_status.drop(op.get_bind(), checkfirst=True)

    op.drop_constraint("fk_organizations_created_by_users", "organizations", type_="foreignkey")
    op.drop_column("organizations", "created_by")
    op.drop_column("organizations", "timezone")
    op.drop_column("organizations", "country")
    op.drop_column("organizations", "logo_url")
    op.drop_column("organizations", "website")
    op.drop_column("organizations", "industry")
