"""Add declarative condition column to risk_rules.

Revision ID: 036
Revises: 035
Create Date: 2026-08-07

"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "036"
down_revision: Union[str, None] = "035"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SAMPLE_CONDITIONS: dict[tuple[str, str], dict] = {
    ("http_headers", "HTTP_NO_CSP"): {"header_missing": "Content-Security-Policy"},
    ("http_headers", "HTTP_NO_HSTS"): {
        "op": "and",
        "conditions": [{"path_truthy": "is_https"}, {"header_missing": "Strict-Transport-Security"}],
    },
    ("robots", "ROBOTS_ADMIN_PATH_DISCLOSED"): {
        "op": "and",
        "conditions": [{"path_truthy": "present"}, {"path_nonempty": "admin_paths"}],
    },
    ("security_txt", "SECURITY_TXT_MISSING"): {"path_falsy": "present"},
}


def upgrade() -> None:
    op.add_column("risk_rules", sa.Column("condition", JSONB, nullable=True))
    op.add_column("risk_rules", sa.Column("rule_code", sa.String(length=32), nullable=True))

    for (plugin, finding_code), condition in _SAMPLE_CONDITIONS.items():
        op.execute(
            sa.text(
                """
                UPDATE risk_rules
                SET condition = CAST(:condition AS jsonb),
                    rule_code = :rule_code,
                    updated_at = now()
                WHERE plugin = :plugin AND finding_code = :finding_code
                """
            ).bindparams(
                plugin=plugin,
                finding_code=finding_code,
                condition=json.dumps(condition),
                rule_code=(
                    "HTTP-001"
                    if finding_code == "HTTP_NO_CSP"
                    else "HTTP-004"
                    if finding_code == "HTTP_NO_HSTS"
                    else None
                ),
            )
        )


def downgrade() -> None:
    op.drop_column("risk_rules", "rule_code")
    op.drop_column("risk_rules", "condition")
