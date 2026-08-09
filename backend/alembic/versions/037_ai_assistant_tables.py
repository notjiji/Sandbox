"""Add AI assistant tables and seed prompt templates.

Revision ID: 037
Revises: 036
Create Date: 2026-08-09

"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "037"
down_revision: Union[str, None] = "036"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PROMPTS: list[tuple[str, str, str]] = [
    (
        "security_explainer",
        "Security Explainer",
        "Explain findings and risk scores from structured scan context only.",
    ),
    (
        "executive_report_writer",
        "Executive Report Writer",
        "Non-technical executive summaries of security posture.",
    ),
    (
        "technical_report_writer",
        "Technical Report Writer",
        "Engineer-focused summaries with protocol and configuration detail.",
    ),
    (
        "remediation_assistant",
        "Remediation Assistant",
        "Actionable remediation guidance for known findings.",
    ),
    (
        "organization_summary",
        "Organization Summary",
        "Organization-wide posture overview for managers.",
    ),
    (
        "finding_comparator",
        "Finding Comparator",
        "Compare two scans and highlight changes.",
    ),
]


def upgrade() -> None:
    op.create_table(
        "ai_conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ai_conversations_organization_id", "ai_conversations", ["organization_id"])
    op.create_index("ix_ai_conversations_user_id", "ai_conversations", ["user_id"])

    op.create_table(
        "ai_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ai_messages_conversation_id", "ai_messages", ["conversation_id"])

    op.create_table(
        "ai_prompts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False, unique=True),
        sa.Column("version", sa.String(length=16), nullable=False, server_default="1.0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ai_prompts_name", "ai_prompts", ["name"], unique=True)

    op.create_table(
        "ai_usage",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ai_usage_organization_id", "ai_usage", ["organization_id"])
    op.create_index("ix_ai_usage_user_id", "ai_usage", ["user_id"])

    prompt_table = sa.table(
        "ai_prompts",
        sa.column("id", UUID(as_uuid=True)),
        sa.column("name", sa.String()),
        sa.column("version", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("system_prompt", sa.Text()),
    )
    from app.services.ai.prompts import PROMPT_TEMPLATES

    rows = [
        {
            "id": uuid.uuid4(),
            "name": name,
            "version": "1.0",
            "description": description,
            "system_prompt": PROMPT_TEMPLATES[name],
        }
        for name, description in _PROMPTS
        if name in PROMPT_TEMPLATES
    ]
    if rows:
        op.bulk_insert(prompt_table, rows)


def downgrade() -> None:
    op.drop_index("ix_ai_usage_user_id", table_name="ai_usage")
    op.drop_index("ix_ai_usage_organization_id", table_name="ai_usage")
    op.drop_table("ai_usage")
    op.drop_index("ix_ai_prompts_name", table_name="ai_prompts")
    op.drop_table("ai_prompts")
    op.drop_index("ix_ai_messages_conversation_id", table_name="ai_messages")
    op.drop_table("ai_messages")
    op.drop_index("ix_ai_conversations_user_id", table_name="ai_conversations")
    op.drop_index("ix_ai_conversations_organization_id", table_name="ai_conversations")
    op.drop_table("ai_conversations")
