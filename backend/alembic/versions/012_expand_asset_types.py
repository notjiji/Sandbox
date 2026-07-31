"""Expand asset_type enum with full digital asset catalog

Revision ID: 012
Revises: 011
Create Date: 2026-07-31

"""
from typing import Sequence, Union

from alembic import op

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_ASSET_TYPES = (
    "windows_server",
    "docker_host",
    "cloud_account",
    "kubernetes_cluster",
    "api_endpoint",
    "mobile_application",
    "git_repository",
    "email_domain",
    "s3_bucket",
    "azure_subscription",
)


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
    for value in NEW_ASSET_TYPES:
        _add_enum_value("asset_type", value)


def downgrade() -> None:
    # PostgreSQL cannot remove enum values without recreating the type.
    pass
