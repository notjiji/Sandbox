"""Asset and organization risk tables, recommendations, scoring fields

Revision ID: 019
Revises: 018
Create Date: 2026-08-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "019"
down_revision: Union[str, None] = "018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
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
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_recommendations_code"), "recommendations", ["code"], unique=True)

    op.add_column("risk_rules", sa.Column("recommendation_id", sa.String(length=32), nullable=True))
    op.create_index(op.f("ix_risk_rules_recommendation_id"), "risk_rules", ["recommendation_id"], unique=False)

    op.add_column("findings", sa.Column("recommendation_id", sa.String(length=32), nullable=True))
    op.create_index(op.f("ix_findings_recommendation_id"), "findings", ["recommendation_id"], unique=False)

    op.create_table(
        "asset_risk",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("asset_id", sa.UUID(), nullable=False),
        sa.Column("scan_id", sa.UUID(), nullable=True),
        sa.Column("total_risk", sa.Float(), nullable=False, server_default="0"),
        sa.Column("score", sa.Float(), nullable=False, server_default="100"),
        sa.Column("grade", sa.String(length=8), nullable=False, server_default="A+"),
        sa.Column("critical_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("high_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("medium_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("low_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_asset_risk_asset_id"), "asset_risk", ["asset_id"], unique=False)
    op.create_index(op.f("ix_asset_risk_scan_id"), "asset_risk", ["scan_id"], unique=False)

    op.create_table(
        "organization_risk",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="100"),
        sa.Column("total_risk", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grade", sa.String(length=8), nullable=False, server_default="A+"),
        sa.Column("risk_level", sa.String(length=32), nullable=False, server_default="Excellent"),
        sa.Column("trend", sa.String(length=16), nullable=False, server_default="stable"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id"),
    )
    op.create_index(
        op.f("ix_organization_risk_organization_id"),
        "organization_risk",
        ["organization_id"],
        unique=True,
    )

    op.create_table(
        "organization_risk_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("total_risk", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grade", sa.String(length=8), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_organization_risk_history_organization_id"),
        "organization_risk_history",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_risk_history_calculated_at"),
        "organization_risk_history",
        ["calculated_at"],
        unique=False,
    )

    # Rename project_risk_metrics.score → total_risk and add security fields
    op.alter_column("project_risk_metrics", "score", new_column_name="total_risk")
    op.add_column(
        "project_risk_metrics",
        sa.Column("security_score", sa.Float(), nullable=False, server_default="100"),
    )
    op.add_column(
        "project_risk_metrics",
        sa.Column("grade", sa.String(length=8), nullable=False, server_default="A+"),
    )
    op.add_column(
        "project_risk_metrics",
        sa.Column("risk_level", sa.String(length=32), nullable=False, server_default="Excellent"),
    )
    op.execute(
        """
        UPDATE project_risk_metrics
        SET security_score = GREATEST(0, 100 - total_risk),
            grade = CASE
                WHEN GREATEST(0, 100 - total_risk) >= 95 THEN 'A+'
                WHEN GREATEST(0, 100 - total_risk) >= 90 THEN 'A'
                WHEN GREATEST(0, 100 - total_risk) >= 80 THEN 'B'
                WHEN GREATEST(0, 100 - total_risk) >= 70 THEN 'C'
                WHEN GREATEST(0, 100 - total_risk) >= 60 THEN 'D'
                ELSE 'F'
            END,
            risk_level = CASE
                WHEN GREATEST(0, 100 - total_risk) >= 90 THEN 'Excellent'
                WHEN GREATEST(0, 100 - total_risk) >= 75 THEN 'Good'
                WHEN GREATEST(0, 100 - total_risk) >= 60 THEN 'Fair'
                WHEN GREATEST(0, 100 - total_risk) >= 40 THEN 'Poor'
                ELSE 'Critical'
            END
        """
    )

    op.execute(
        """
        INSERT INTO recommendations (id, code, text) VALUES
            (gen_random_uuid(), 'REC-021', 'Implement a Content-Security-Policy header to reduce XSS risk.'),
            (gen_random_uuid(), 'REC-022', 'Enable HTTP Strict Transport Security (HSTS) to enforce HTTPS.'),
            (gen_random_uuid(), 'REC-023', 'Renew or replace the expired SSL/TLS certificate immediately.'),
            (gen_random_uuid(), 'REC-024', 'Disable TLS 1.0 and other legacy protocol versions.'),
            (gen_random_uuid(), 'REC-025', 'Close or restrict access to insecure services such as Telnet.'),
            (gen_random_uuid(), 'REC-026', 'Publish an SPF record to protect against email spoofing.'),
            (gen_random_uuid(), 'REC-027', 'Renew domain registration before expiration.')
        """
    )

    op.execute(
        """
        UPDATE risk_rules SET recommendation_id = 'REC-021' WHERE finding_code = 'HTTP_NO_CSP';
        UPDATE risk_rules SET recommendation_id = 'REC-022', score = 25 WHERE finding_code = 'HTTP_NO_HSTS';
        UPDATE risk_rules SET recommendation_id = 'REC-023' WHERE finding_code = 'SSL_EXPIRED';
        UPDATE risk_rules SET recommendation_id = 'REC-024' WHERE finding_code = 'SSL_TLS10_ENABLED';
        UPDATE risk_rules SET recommendation_id = 'REC-025', score = 50 WHERE finding_code = 'PORT_TELNET_OPEN';
        UPDATE risk_rules SET recommendation_id = 'REC-026', score = 15 WHERE finding_code = 'DNS_MISSING_SPF';
        UPDATE risk_rules SET recommendation_id = 'REC-027' WHERE finding_code = 'WHOIS_EXPIRING_SOON';
        """
    )


def downgrade() -> None:
    op.drop_column("project_risk_metrics", "risk_level")
    op.drop_column("project_risk_metrics", "grade")
    op.drop_column("project_risk_metrics", "security_score")
    op.alter_column("project_risk_metrics", "total_risk", new_column_name="score")
    op.drop_index(op.f("ix_organization_risk_history_calculated_at"), table_name="organization_risk_history")
    op.drop_index(op.f("ix_organization_risk_history_organization_id"), table_name="organization_risk_history")
    op.drop_table("organization_risk_history")
    op.drop_index(op.f("ix_organization_risk_organization_id"), table_name="organization_risk")
    op.drop_table("organization_risk")
    op.drop_index(op.f("ix_asset_risk_scan_id"), table_name="asset_risk")
    op.drop_index(op.f("ix_asset_risk_asset_id"), table_name="asset_risk")
    op.drop_table("asset_risk")
    op.drop_index(op.f("ix_findings_recommendation_id"), table_name="findings")
    op.drop_column("findings", "recommendation_id")
    op.drop_index(op.f("ix_risk_rules_recommendation_id"), table_name="risk_rules")
    op.drop_column("risk_rules", "recommendation_id")
    op.drop_index(op.f("ix_recommendations_code"), table_name="recommendations")
    op.drop_table("recommendations")
