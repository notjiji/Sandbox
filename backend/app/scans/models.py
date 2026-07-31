import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.scans.enums import ScanStatus, ScanType


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
    status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus, name="scan_status", native_enum=True),
        nullable=False,
        default=ScanStatus.PENDING,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="scans")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="scans")
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="scan")
