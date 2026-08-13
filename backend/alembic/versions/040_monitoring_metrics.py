"""Normalized monitoring metrics table.

Revision ID: 040
Revises: 039_monitoring_agent
Create Date: 2026-08-13
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "040_monitoring_metrics"
down_revision: Union[str, None] = "039_monitoring_agent"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "monitoring_metrics",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("asset_id", sa.UUID(), nullable=False),
        sa.Column("metric_type", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("labels", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["monitoring_agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitoring_metrics_agent_id", "monitoring_metrics", ["agent_id"])
    op.create_index("ix_monitoring_metrics_asset_id", "monitoring_metrics", ["asset_id"])
    op.create_index("ix_monitoring_metrics_metric_type", "monitoring_metrics", ["metric_type"])
    op.create_index("ix_monitoring_metrics_collected_at", "monitoring_metrics", ["collected_at"])
    op.create_index(
        "ix_monitoring_metrics_asset_type_time",
        "monitoring_metrics",
        ["asset_id", "metric_type", "collected_at"],
    )

    conn = op.get_bind()
    snapshots = conn.execute(
        sa.text(
            """
            SELECT id, agent_id, asset_id, collected_at,
                   cpu_percent, ram_percent, ram_used_mb, ram_total_mb,
                   disk_percent, disk_used_gb, disk_total_gb,
                   uptime_seconds, load_avg_1, process_count
            FROM monitoring_snapshots
            """
        )
    ).mappings()

    insert = sa.text(
        """
        INSERT INTO monitoring_metrics
            (id, agent_id, asset_id, metric_type, value, unit, collected_at, labels)
        VALUES
            (gen_random_uuid(), :agent_id, :asset_id, :metric_type, :value, :unit, :collected_at, CAST(:labels AS jsonb))
        """
    )
    for row in snapshots:
        points = [
            ("cpu_usage", row["cpu_percent"], "percent", None),
            ("memory_usage", row["ram_percent"], "percent", None),
            ("memory_used", row["ram_used_mb"], "mb", None),
            ("memory_total", row["ram_total_mb"], "mb", None),
            ("disk_usage", row["disk_percent"], "percent", '{"filesystem": "/"}'),
            ("disk_used", row["disk_used_gb"], "gb", '{"filesystem": "/"}'),
            ("disk_total", row["disk_total_gb"], "gb", '{"filesystem": "/"}'),
            ("load_average", row["load_avg_1"], "ratio", None),
            ("uptime", row["uptime_seconds"], "seconds", None),
            ("process_count", row["process_count"], "count", None),
        ]
        for metric_type, value, unit, labels in points:
            if value is None:
                continue
            conn.execute(
                insert,
                {
                    "agent_id": row["agent_id"],
                    "asset_id": row["asset_id"],
                    "metric_type": metric_type,
                    "value": float(value),
                    "unit": unit,
                    "collected_at": row["collected_at"],
                    "labels": labels,
                },
            )

    op.drop_column("monitoring_snapshots", "cpu_percent")
    op.drop_column("monitoring_snapshots", "ram_percent")
    op.drop_column("monitoring_snapshots", "ram_used_mb")
    op.drop_column("monitoring_snapshots", "ram_total_mb")
    op.drop_column("monitoring_snapshots", "disk_percent")
    op.drop_column("monitoring_snapshots", "disk_used_gb")
    op.drop_column("monitoring_snapshots", "disk_total_gb")
    op.drop_column("monitoring_snapshots", "uptime_seconds")
    op.drop_column("monitoring_snapshots", "load_avg_1")
    op.drop_column("monitoring_snapshots", "process_count")


def downgrade() -> None:
    op.add_column("monitoring_snapshots", sa.Column("cpu_percent", sa.Float(), nullable=True))
    op.add_column("monitoring_snapshots", sa.Column("ram_percent", sa.Float(), nullable=True))
    op.add_column("monitoring_snapshots", sa.Column("ram_used_mb", sa.Float(), nullable=True))
    op.add_column("monitoring_snapshots", sa.Column("ram_total_mb", sa.Float(), nullable=True))
    op.add_column("monitoring_snapshots", sa.Column("disk_percent", sa.Float(), nullable=True))
    op.add_column("monitoring_snapshots", sa.Column("disk_used_gb", sa.Float(), nullable=True))
    op.add_column("monitoring_snapshots", sa.Column("disk_total_gb", sa.Float(), nullable=True))
    op.add_column("monitoring_snapshots", sa.Column("uptime_seconds", sa.Integer(), nullable=True))
    op.add_column("monitoring_snapshots", sa.Column("load_avg_1", sa.Float(), nullable=True))
    op.add_column("monitoring_snapshots", sa.Column("process_count", sa.Integer(), nullable=True))

    op.drop_index("ix_monitoring_metrics_asset_type_time", table_name="monitoring_metrics")
    op.drop_index("ix_monitoring_metrics_collected_at", table_name="monitoring_metrics")
    op.drop_index("ix_monitoring_metrics_metric_type", table_name="monitoring_metrics")
    op.drop_index("ix_monitoring_metrics_asset_id", table_name="monitoring_metrics")
    op.drop_index("ix_monitoring_metrics_agent_id", table_name="monitoring_metrics")
    op.drop_table("monitoring_metrics")
