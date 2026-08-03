import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.findings.enums import FindingSeverity
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RiskRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "risk_rules"
    __table_args__ = (UniqueConstraint("plugin", "finding_code", name="uq_risk_rules_plugin_code"),)

    plugin: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    finding_code: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[FindingSeverity] = mapped_column(
        Enum(FindingSeverity, name="finding_severity", native_enum=True),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ProjectRiskMetric(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "project_risk_metrics"

    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    open_findings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    top_issues: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    project: Mapped["Project"] = relationship("Project")
