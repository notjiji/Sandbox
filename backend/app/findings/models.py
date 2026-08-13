import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.findings.constants import FINDING_SOURCE_SCAN
from app.findings.enums import FindingSeverity, FindingStatus
from app.shared.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Finding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "findings"

    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=FINDING_SOURCE_SCAN,
        index=True,
    )
    plugin: Mapped[str | None] = mapped_column(String(128), nullable=True)
    finding_code: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    check_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[FindingSeverity] = mapped_column(
        Enum(FindingSeverity, name="finding_severity", native_enum=True),
        nullable=False,
        default=FindingSeverity.MEDIUM,
    )
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[FindingStatus] = mapped_column(
        Enum(FindingStatus, name="finding_status", native_enum=True),
        nullable=False,
        default=FindingStatus.OPEN,
    )
    recommendation_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    references: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    cvss: Mapped[float | None] = mapped_column(Float, nullable=True)
    cwe: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cve: Mapped[str | None] = mapped_column(String(32), nullable=True)
    detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="findings")
    scan: Mapped["Scan | None"] = relationship("Scan", back_populates="findings")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="findings")
