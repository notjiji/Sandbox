"""Risk rules, finding codes, and stored project risk metrics

Revision ID: 018
Revises: 017
Create Date: 2026-08-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

finding_severity = postgresql.ENUM(
    "critical",
    "high",
    "medium",
    "low",
    "info",
    name="finding_severity",
    create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "risk_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("plugin", sa.String(length=128), nullable=False),
        sa.Column("finding_code", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", finding_severity, nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plugin", "finding_code", name="uq_risk_rules_plugin_code"),
    )
    op.create_index(op.f("ix_risk_rules_plugin"), "risk_rules", ["plugin"], unique=False)
    op.create_index(op.f("ix_risk_rules_finding_code"), "risk_rules", ["finding_code"], unique=False)

    op.create_table(
        "project_risk_metrics",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("open_findings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("top_issues", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_project_risk_metrics_project_id"),
        "project_risk_metrics",
        ["project_id"],
        unique=False,
    )

    op.add_column("findings", sa.Column("finding_code", sa.String(length=128), nullable=True))
    op.add_column("findings", sa.Column("check_status", sa.String(length=32), nullable=True))
    op.add_column(
        "findings",
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0"),
    )
    op.create_index(op.f("ix_findings_finding_code"), "findings", ["finding_code"], unique=False)

    op.execute(
        """
        INSERT INTO risk_rules (id, plugin, finding_code, title, description, severity, score, enabled)
        VALUES
            (gen_random_uuid(), 'http_headers', 'HTTP_NO_CSP', 'Missing Content-Security-Policy', 'Response lacks a Content-Security-Policy header.', 'medium', 15, true),
            (gen_random_uuid(), 'http_headers', 'HTTP_NO_HSTS', 'Missing Strict-Transport-Security', 'Response lacks an HSTS header.', 'high', 25, true),
            (gen_random_uuid(), 'ssl', 'SSL_EXPIRED', 'Expired SSL Certificate', 'The TLS certificate is expired.', 'critical', 50, true),
            (gen_random_uuid(), 'ssl', 'SSL_TLS10_ENABLED', 'TLS 1.0 Enabled', 'Legacy TLS 1.0 is still enabled.', 'high', 30, true),
            (gen_random_uuid(), 'ports', 'PORT_TELNET_OPEN', 'Telnet Port Open', 'Telnet service detected on an open port.', 'critical', 45, true),
            (gen_random_uuid(), 'dns', 'DNS_MISSING_SPF', 'Missing SPF Record', 'No SPF record found for the domain.', 'medium', 10, true),
            (gen_random_uuid(), 'whois', 'WHOIS_EXPIRING_SOON', 'Domain Expiring Soon', 'WHOIS registration expires within 30 days.', 'low', 5, true)
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_findings_finding_code"), table_name="findings")
    op.drop_column("findings", "risk_score")
    op.drop_column("findings", "check_status")
    op.drop_column("findings", "finding_code")
    op.drop_index(op.f("ix_project_risk_metrics_project_id"), table_name="project_risk_metrics")
    op.drop_table("project_risk_metrics")
    op.drop_index(op.f("ix_risk_rules_finding_code"), table_name="risk_rules")
    op.drop_index(op.f("ix_risk_rules_plugin"), table_name="risk_rules")
    op.drop_table("risk_rules")
