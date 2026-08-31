import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.monitoring.enums import AgentStatus, AlertSeverity, AlertStatus
from app.shared.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum


class MonitoringAgent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "monitoring_agents"
    __table_args__ = (UniqueConstraint("asset_id", name="uq_monitoring_agents_asset_id"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    enrollment_token_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    enrollment_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    credential_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    status: Mapped[AgentStatus] = mapped_column(
        pg_enum(AgentStatus, "agent_status"),
        nullable=False,
        default=AgentStatus.PENDING,
    )
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agent_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    snapshots: Mapped[list["MonitoringSnapshot"]] = relationship(
        "MonitoringSnapshot",
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    metrics: Mapped[list["MonitoringMetric"]] = relationship(
        "MonitoringMetric",
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list["MonitoringAlert"]] = relationship(
        "MonitoringAlert",
        back_populates="agent",
        cascade="all, delete-orphan",
    )


class MonitoringSnapshot(Base, UUIDPrimaryKeyMixin):
    """Heartbeat document: latest payload (services, security, processes). Numeric series live in MonitoringMetric."""

    __tablename__ = "monitoring_snapshots"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("monitoring_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    agent: Mapped["MonitoringAgent"] = relationship("MonitoringAgent", back_populates="snapshots")


class MonitoringMetric(Base, UUIDPrimaryKeyMixin):
    """Normalized time-series point. New collectors add a metric_type, not a column."""

    __tablename__ = "monitoring_metrics"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("monitoring_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    labels: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    agent: Mapped["MonitoringAgent"] = relationship("MonitoringAgent", back_populates="metrics")


class MonitoringAlert(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "monitoring_alerts"
    __table_args__ = (
        UniqueConstraint("asset_id", "alert_code", name="uq_monitoring_alerts_asset_code"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("monitoring_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alert_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[AlertSeverity] = mapped_column(
        pg_enum(AlertSeverity, "monitoring_alert_severity"),
        nullable=False,
        default=AlertSeverity.MEDIUM,
    )
    status: Mapped[AlertStatus] = mapped_column(
        pg_enum(AlertStatus, "monitoring_alert_status"),
        nullable=False,
        default=AlertStatus.OPEN,
        index=True,
    )
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    agent: Mapped["MonitoringAgent"] = relationship("MonitoringAgent", back_populates="alerts")
