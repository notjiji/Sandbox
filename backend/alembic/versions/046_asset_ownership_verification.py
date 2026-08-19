"""Add asset ownership verification fields.

Revision ID: 046
Revises: 045_audit_log_hash_chain
Create Date: 2026-08-19
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "046_asset_ownership_verification"
down_revision: Union[str, None] = "045_audit_log_hash_chain"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("assets", sa.Column("verification_method", sa.String(length=32), nullable=True))
    op.add_column(
        "assets",
        sa.Column(
            "verification_status",
            sa.String(length=32),
            nullable=False,
            server_default="unverified",
        ),
    )
    op.add_column("assets", sa.Column("verification_token", sa.String(length=128), nullable=True))
    op.add_column("assets", sa.Column("verification_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("assets", sa.Column("verification_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("assets", sa.Column("verification_last_error", sa.Text(), nullable=True))
    op.create_index("ix_assets_verification_status", "assets", ["verification_status"])


def downgrade() -> None:
    op.drop_index("ix_assets_verification_status", table_name="assets")
    op.drop_column("assets", "verification_last_error")
    op.drop_column("assets", "verification_verified_at")
    op.drop_column("assets", "verification_requested_at")
    op.drop_column("assets", "verification_token")
    op.drop_column("assets", "verification_status")
    op.drop_column("assets", "verification_method")
