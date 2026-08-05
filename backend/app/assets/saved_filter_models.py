import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AssetSavedFilter(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "asset_saved_filters"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", "name", name="uq_asset_saved_filters_project_user_name"),
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
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    filters_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    project: Mapped["Project"] = relationship("Project")
    user: Mapped["User"] = relationship("User")
