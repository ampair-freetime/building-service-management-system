"""Immutable audit records for staff accounts removed from active use."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StaffDeletionAudit(Base):
    """Stores identity snapshots without foreign keys that deletion could invalidate."""

    __tablename__ = "staff_deletion_audit"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    deleted_staff_id: Mapped[UUID] = mapped_column(Uuid, index=True)
    deleted_email: Mapped[str] = mapped_column(String(255))
    deleted_full_name: Mapped[str] = mapped_column(String(150))
    deleted_role: Mapped[str] = mapped_column(String(30))
    deleted_by_staff_id: Mapped[UUID] = mapped_column(Uuid, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
