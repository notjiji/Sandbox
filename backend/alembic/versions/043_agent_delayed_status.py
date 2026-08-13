"""Add delayed agent liveness status.

Revision ID: 043
Revises: 042_alerts_vs_findings
Create Date: 2026-08-13
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "043_agent_delayed_status"
down_revision: Union[str, None] = "042_alerts_vs_findings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE agent_status ADD VALUE IF NOT EXISTS 'delayed'")


def downgrade() -> None:
    # PostgreSQL cannot easily remove enum values.
    pass
