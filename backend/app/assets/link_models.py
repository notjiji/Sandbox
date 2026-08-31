import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.assets.enums import AssetLinkType
from app.shared.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum


class AssetLink(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Peer relationship between two assets (beyond parent/child hierarchy)."""

    __tablename__ = "asset_links"
    __table_args__ = (
        UniqueConstraint(
            "source_asset_id",
            "target_asset_id",
            "link_type",
            name="uq_asset_links_source_target_type",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_asset_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_asset_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    link_type: Mapped[AssetLinkType] = mapped_column(
        pg_enum(AssetLinkType, "asset_link_type"),
        nullable=False,
    )
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    source_asset: Mapped["Asset"] = relationship(
        "Asset",
        foreign_keys=[source_asset_id],
        back_populates="outbound_links",
    )
    target_asset: Mapped["Asset"] = relationship(
        "Asset",
        foreign_keys=[target_asset_id],
        back_populates="inbound_links",
    )
