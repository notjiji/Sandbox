"""update organization roles for RBAC

Revision ID: 005
Revises: 004
Create Date: 2026-07-29

"""
from typing import Sequence, Union

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TYPE organization_role_new AS ENUM (
            'owner', 'admin', 'security_analyst', 'manager', 'viewer'
        )
        """
    )
    op.execute(
        """
        ALTER TABLE organization_members
        ALTER COLUMN role TYPE organization_role_new
        USING (
            CASE role::text
                WHEN 'member' THEN 'security_analyst'::organization_role_new
                ELSE role::text::organization_role_new
            END
        )
        """
    )
    op.execute("DROP TYPE organization_role")
    op.execute("ALTER TYPE organization_role_new RENAME TO organization_role")


def downgrade() -> None:
    op.execute(
        """
        CREATE TYPE organization_role_old AS ENUM (
            'owner', 'admin', 'member', 'viewer'
        )
        """
    )
    op.execute(
        """
        ALTER TABLE organization_members
        ALTER COLUMN role TYPE organization_role_old
        USING (
            CASE role::text
                WHEN 'security_analyst' THEN 'member'::organization_role_old
                WHEN 'manager' THEN 'viewer'::organization_role_old
                ELSE role::text::organization_role_old
            END
        )
        """
    )
    op.execute("DROP TYPE organization_role")
    op.execute("ALTER TYPE organization_role_old RENAME TO organization_role")
