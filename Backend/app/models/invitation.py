"""Invitation records for first-time staff password setup."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.staff import Staff


class StaffInvitation(Base):
    """Stores a hashed, single-use activation token and its delivery outcome."""

    __tablename__ = "staff_invitations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    staff_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("staff.id", ondelete="CASCADE"), index=True
    )
    # The raw token exists only while composing the email; a database leak cannot
    # directly be used to activate an account.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_status: Mapped[str] = mapped_column(String(20), default="pending")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    staff: Mapped["Staff"] = relationship(back_populates="invitations")
