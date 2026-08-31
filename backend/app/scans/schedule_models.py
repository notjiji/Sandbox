import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum
from app.scans.enums import SchedulePreset, ScanType


class AssetScanSchedule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "asset_scan_schedules"
    __table_args__ = (
        UniqueConstraint("asset_id", "preset", name="uq_asset_scan_schedules_asset_preset"),
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
    preset: Mapped[SchedulePreset] = mapped_column(
        pg_enum(SchedulePreset, "schedule_preset"),
        nullable=False,
    )
    scan_type: Mapped[ScanType] = mapped_column(
        pg_enum(ScanType, "scan_type", create_constraint=False),
        nullable=False,
    )
    selected_plugins: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_scan_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="SET NULL"),
        nullable=True,
    )

    asset: Mapped["Asset"] = relationship("Asset", back_populates="scan_schedules")
    project: Mapped["Project"] = relationship("Project")
    last_scan: Mapped["Scan | None"] = relationship("Scan", foreign_keys=[last_scan_id])
