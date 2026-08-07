"""Risk domain models — rules, recommendations, asset/org risk snapshots."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.findings.enums import FindingSeverity
from app.shared.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Recommendation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "recommendations"

    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)


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
    recommendation_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    rule_code: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    condition: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ProjectRiskMetric(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "project_risk_metrics"

    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    total_risk: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    security_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    grade: Mapped[str] = mapped_column(String(8), nullable=False, default="A+")
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="Excellent")
    open_findings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    top_issues: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    project: Mapped["Project"] = relationship("Project")


class AssetRisk(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "asset_risk"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    total_risk: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    grade: Mapped[str] = mapped_column(String(8), nullable=False, default="A+")
    critical_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    high_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    medium_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    asset: Mapped["Asset"] = relationship("Asset")


class OrganizationRisk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organization_risk"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    total_risk: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    grade: Mapped[str] = mapped_column(String(8), nullable=False, default="A+")
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="Excellent")
    trend: Mapped[str] = mapped_column(String(16), nullable=False, default="stable")


class OrganizationRiskHistory(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "organization_risk_history"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    total_risk: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    grade: Mapped[str] = mapped_column(String(8), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
