"""user is_verified and token revoked/created_at

Revision ID: 004
Revises: 003
Create Date: 2026-07-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.add_column(
        "refresh_tokens",
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "refresh_tokens",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.execute(
        """
        UPDATE refresh_tokens
        SET revoked = true
        WHERE revoked_at IS NOT NULL
        """
    )

    op.add_column(
        "password_reset_tokens",
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "password_reset_tokens",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.execute(
        """
        UPDATE password_reset_tokens
        SET revoked = true
        WHERE used_at IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_column("password_reset_tokens", "created_at")
    op.drop_column("password_reset_tokens", "revoked")
    op.drop_column("refresh_tokens", "created_at")
    op.drop_column("refresh_tokens", "revoked")
    op.drop_column("users", "is_verified")
