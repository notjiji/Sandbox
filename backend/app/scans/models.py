import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.scans.enums import ScanStatus, ScanType, PluginRunStatus


class Scan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scans"

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
    scan_type: Mapped[ScanType] = mapped_column(
        Enum(ScanType, name="scan_type", native_enum=True),
        nullable=False,
        default=ScanType.FULL,
    )
    selected_plugins: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus, name="scan_status", native_enum=True),
        nullable=False,
        default=ScanStatus.PENDING,
    )
    pending_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    running_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    project: Mapped["Project"] = relationship("Project", back_populates="scans")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="scans")
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="scan")
    plugin_runs: Mapped[list["ScanPluginRun"]] = relationship(
        "ScanPluginRun",
        back_populates="scan",
        cascade="all, delete-orphan",
    )


class ScanPluginRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scan_plugin_runs"

    scan_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plugin_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[PluginRunStatus] = mapped_column(
        Enum(PluginRunStatus, name="plugin_run_status", native_enum=True),
        nullable=False,
        default=PluginRunStatus.PENDING,
    )
    error_message: Mapped[str | None] = mapped_column(nullable=True)
    findings_count: Mapped[int] = mapped_column(nullable=False, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    scan: Mapped["Scan"] = relationship("Scan", back_populates="plugin_runs")
    asset: Mapped["Asset"] = relationship("Asset")
