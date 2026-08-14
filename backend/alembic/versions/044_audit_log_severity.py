"""Add severity and resource_id index to audit_logs.

Revision ID: 044
Revises: 043_agent_delayed_status
Create Date: 2026-08-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "044_audit_log_severity"
down_revision: Union[str, None] = "043_agent_delayed_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "audit_logs",
        sa.Column(
            "severity",
            sa.String(length=16),
            nullable=False,
            server_default="info",
        ),
    )
    op.create_index("ix_audit_logs_severity", "audit_logs", ["severity"])
    op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_resource_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_severity", table_name="audit_logs")
    op.drop_column("audit_logs", "severity")
