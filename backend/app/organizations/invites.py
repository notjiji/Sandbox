import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.members.enums import OrganizationRole
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class InviteStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class OrganizationInvite(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organization_invites"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    role: Mapped[OrganizationRole] = mapped_column(
        Enum(OrganizationRole, name="organization_role", native_enum=True),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    invited_by: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    membership_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organization_members.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[InviteStatus] = mapped_column(
        Enum(InviteStatus, name="invite_status", native_enum=True),
        nullable=False,
        default=InviteStatus.PENDING,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped["Organization"] = relationship("Organization")
    inviter: Mapped["User"] = relationship("User", foreign_keys=[invited_by])
    membership: Mapped["OrganizationMember | None"] = relationship(
        "OrganizationMember",
        foreign_keys=[membership_id],
    )
