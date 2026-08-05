import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.assets.enums import (
    AssetCategory,
    AssetCriticality,
    AssetEnvironment,
    AssetStatus,
    AssetType,
)
from app.shared.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Asset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A digital asset belonging to a project — owned by the Asset Service."""

    __tablename__ = "assets"

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
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, name="asset_type", native_enum=True),
        nullable=False,
        default=AssetType.WEBSITE,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, name="asset_status", native_enum=True),
        nullable=False,
        default=AssetStatus.PENDING,
    )
    environment: Mapped[AssetEnvironment] = mapped_column(
        Enum(AssetEnvironment, name="asset_environment", native_enum=True),
        nullable=False,
        default=AssetEnvironment.PRODUCTION,
    )
    criticality: Mapped[AssetCriticality] = mapped_column(
        Enum(AssetCriticality, name="asset_criticality", native_enum=True),
        nullable=False,
        default=AssetCriticality.MEDIUM,
    )
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_identifier: Mapped[str | None] = mapped_column(String(512), nullable=True)
    business_unit: Mapped[str | None] = mapped_column(String(128), nullable=True)
    asset_category: Mapped[AssetCategory | None] = mapped_column(
        Enum(AssetCategory, name="asset_category", native_enum=True),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped["Organization"] = relationship("Organization")
    project: Mapped["Project"] = relationship("Project", back_populates="assets")
    parent: Mapped["Asset | None"] = relationship(
        "Asset", remote_side="Asset.id", back_populates="children"
    )
    children: Mapped[list["Asset"]] = relationship(
        "Asset", back_populates="parent", cascade="all, delete-orphan"
    )
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])
    updater: Mapped["User | None"] = relationship("User", foreign_keys=[updated_by])
    archiver: Mapped["User | None"] = relationship("User", foreign_keys=[archived_by])
    metadata_entries: Mapped[list["AssetMetadataEntry"]] = relationship(
        "AssetMetadataEntry",
        back_populates="asset",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list["AssetTag"]] = relationship(
        "AssetTag",
        back_populates="asset",
        cascade="all, delete-orphan",
    )
    scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="asset")
    scan_schedules: Mapped[list["AssetScanSchedule"]] = relationship(
        "AssetScanSchedule",
        back_populates="asset",
        cascade="all, delete-orphan",
    )
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="asset")
    outbound_links: Mapped[list["AssetLink"]] = relationship(
        "AssetLink",
        foreign_keys="AssetLink.source_asset_id",
        back_populates="source_asset",
        cascade="all, delete-orphan",
    )
    inbound_links: Mapped[list["AssetLink"]] = relationship(
        "AssetLink",
        foreign_keys="AssetLink.target_asset_id",
        back_populates="target_asset",
        cascade="all, delete-orphan",
    )


class AssetMetadataEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Type-specific key/value metadata for an asset."""

    __tablename__ = "asset_metadata"
    __table_args__ = (
        UniqueConstraint("asset_id", "key", name="uq_asset_metadata_asset_key"),
    )

    asset_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="metadata_entries")


class AssetTag(Base, UUIDPrimaryKeyMixin):
    """Unlimited tags attached to an asset for search and filtering."""

    __tablename__ = "asset_tags"
    __table_args__ = (
        UniqueConstraint("asset_id", "tag", name="uq_asset_tags_asset_tag"),
    )

    asset_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    asset: Mapped["Asset"] = relationship("Asset", back_populates="tags")
