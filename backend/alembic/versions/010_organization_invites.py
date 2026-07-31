"""organization_invites table for email-based invitations

Revision ID: 010
Revises: 009
Create Date: 2026-07-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

organization_role = postgresql.ENUM(
    "owner",
    "admin",
    "security_analyst",
    "manager",
    "viewer",
    name="organization_role",
    create_type=False,
)
invite_status = postgresql.ENUM(
    "pending",
    "accepted",
    "revoked",
    "expired",
    name="invite_status",
    create_type=False,
)


def upgrade() -> None:
    invite_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "organization_invites",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("role", organization_role, nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("invited_by", sa.UUID(), nullable=False),
        sa.Column("membership_id", sa.UUID(), nullable=True),
        sa.Column(
            "status",
            invite_status,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["membership_id"],
            ["organization_members.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_organization_invites_token_hash"),
    )
    op.create_index(
        op.f("ix_organization_invites_organization_id"),
        "organization_invites",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_invites_email"),
        "organization_invites",
        ["email"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_organization_invites_email"), table_name="organization_invites")
    op.drop_index(
        op.f("ix_organization_invites_organization_id"),
        table_name="organization_invites",
    )
    op.drop_table("organization_invites")
    invite_status.drop(op.get_bind(), checkfirst=True)
