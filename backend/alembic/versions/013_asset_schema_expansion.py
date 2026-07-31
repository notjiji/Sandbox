"""Asset schema expansion — metadata, tags, lifecycle, environment, criticality

Revision ID: 013
Revises: 012
Create Date: 2026-07-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

asset_environment = postgresql.ENUM(
    "production",
    "staging",
    "development",
    "testing",
    name="asset_environment",
    create_type=False,
)
asset_criticality = postgresql.ENUM(
    "critical",
    "high",
    "medium",
    "low",
    name="asset_criticality",
    create_type=False,
)

PRIMARY_METADATA_KEY_SQL = """
CASE type::text
    WHEN 'website' THEN 'url'
    WHEN 'domain' THEN 'domain'
    WHEN 'public_ip' THEN 'address'
    WHEN 'server' THEN 'hostname'
    WHEN 'windows_server' THEN 'hostname'
    WHEN 'docker_host' THEN 'hostname'
    WHEN 'cloud_account' THEN 'account_id'
    WHEN 'kubernetes_cluster' THEN 'cluster'
    WHEN 'api_endpoint' THEN 'endpoint'
    WHEN 'mobile_application' THEN 'bundle_id'
    WHEN 'git_repository' THEN 'repository'
    WHEN 'email_domain' THEN 'email_domain'
    WHEN 's3_bucket' THEN 'bucket'
    WHEN 'azure_subscription' THEN 'subscription_id'
    ELSE 'identifier'
END
"""


def _add_enum_value(enum_name: str, value: str) -> None:
    op.execute(
        f"""
        DO $$ BEGIN
            ALTER TYPE {enum_name} ADD VALUE '{value}';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    )


def upgrade() -> None:
    asset_environment.create(op.get_bind(), checkfirst=True)
    asset_criticality.create(op.get_bind(), checkfirst=True)

    _add_enum_value("asset_status", "pending")
    _add_enum_value("asset_status", "deleted")
    op.execute("UPDATE assets SET status = 'archived' WHERE status = 'inactive'")

    op.add_column("assets", sa.Column("organization_id", sa.UUID(), nullable=True))
    op.add_column("assets", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "assets",
        sa.Column(
            "environment",
            asset_environment,
            nullable=False,
            server_default="production",
        ),
    )
    op.add_column(
        "assets",
        sa.Column(
            "criticality",
            asset_criticality,
            nullable=False,
            server_default="medium",
        ),
    )
    op.add_column("assets", sa.Column("owner", sa.String(length=255), nullable=True))
    op.add_column("assets", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    op.execute(
        """
        UPDATE assets AS a
        SET organization_id = p.organization_id
        FROM projects AS p
        WHERE a.project_id = p.id
        """
    )
    op.alter_column("assets", "organization_id", nullable=False)
    op.create_index(op.f("ix_assets_organization_id"), "assets", ["organization_id"], unique=False)
    op.create_foreign_key(
        "fk_assets_organization_id_organizations",
        "assets",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_table(
        "asset_metadata",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("asset_id", sa.UUID(), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
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
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", "key", name="uq_asset_metadata_asset_key"),
    )
    op.create_index(op.f("ix_asset_metadata_asset_id"), "asset_metadata", ["asset_id"], unique=False)

    op.execute(
        f"""
        INSERT INTO asset_metadata (id, asset_id, key, value, created_at, updated_at)
        SELECT gen_random_uuid(), id, {PRIMARY_METADATA_KEY_SQL}, identifier, now(), now()
        FROM assets
        WHERE identifier IS NOT NULL AND btrim(identifier) <> ''
        """
    )

    op.create_table(
        "asset_tags",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("asset_id", sa.UUID(), nullable=False),
        sa.Column("tag", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", "tag", name="uq_asset_tags_asset_tag"),
    )
    op.create_index(op.f("ix_asset_tags_asset_id"), "asset_tags", ["asset_id"], unique=False)

    op.drop_column("assets", "identifier")


def downgrade() -> None:
    op.add_column("assets", sa.Column("identifier", sa.String(length=512), nullable=True))

    op.execute(
        f"""
        UPDATE assets AS a
        SET identifier = m.value
        FROM asset_metadata AS m
        WHERE m.asset_id = a.id
          AND m.key = ({PRIMARY_METADATA_KEY_SQL.replace('type::text', 'a.type::text')})
        """
    )

    op.drop_index(op.f("ix_asset_tags_asset_id"), table_name="asset_tags")
    op.drop_table("asset_tags")
    op.drop_index(op.f("ix_asset_metadata_asset_id"), table_name="asset_metadata")
    op.drop_table("asset_metadata")

    op.drop_constraint("fk_assets_organization_id_organizations", "assets", type_="foreignkey")
    op.drop_index(op.f("ix_assets_organization_id"), table_name="assets")
    op.drop_column("assets", "deleted_at")
    op.drop_column("assets", "owner")
    op.drop_column("assets", "criticality")
    op.drop_column("assets", "environment")
    op.drop_column("assets", "description")
    op.drop_column("assets", "organization_id")

    op.execute("UPDATE assets SET status = 'active' WHERE status = 'pending'")
    op.execute("UPDATE assets SET status = 'archived' WHERE status = 'deleted'")

    asset_criticality.drop(op.get_bind(), checkfirst=True)
    asset_environment.drop(op.get_bind(), checkfirst=True)
