import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AssetType(str, enum.Enum):
    HOST = "host"
    DOMAIN = "domain"
    IP = "ip"
    APPLICATION = "application"


class AssetStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Asset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assets"

    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    identifier: Mapped[str | None] = mapped_column(String(512), nullable=True)
    type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, name="asset_type", native_enum=True),
        nullable=False,
        default=AssetType.HOST,
    )
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, name="asset_status", native_enum=True),
        nullable=False,
        default=AssetStatus.ACTIVE,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    project: Mapped["Project"] = relationship("Project", back_populates="assets")
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])
    scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="asset")
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="asset")
