"""email verification OTP table

Revision ID: 006
Revises: 005
Create Date: 2026-07-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_verification_otps",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("otp_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_email_verification_otps_user_id"),
        "email_verification_otps",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_email_verification_otps_otp_hash"),
        "email_verification_otps",
        ["otp_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_email_verification_otps_otp_hash"), table_name="email_verification_otps")
    op.drop_index(op.f("ix_email_verification_otps_user_id"), table_name="email_verification_otps")
    op.drop_table("email_verification_otps")
