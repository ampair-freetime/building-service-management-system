"""SQLAlchemy model สำหรับบัญชีพนักงาน."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AccountStatus, StaffRole


class Staff(Base):
    """บัญชี Technician, Housekeeper, Adminnistrative และ Admin."""

    __tablename__ = "staff"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    staff_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150))
    role: Mapped[StaffRole] = mapped_column(
        SqlEnum(
            StaffRole,
            name="staff_role",
            values_callable=lambda values: [value.value for value in values],
        ),
        index=True,
    )
    status: Mapped[AccountStatus] = mapped_column(
        SqlEnum(
            AccountStatus,
            name="account_status",
            values_callable=lambda values: [value.value for value in values],
        ),
        default=AccountStatus.ACTIVE,
        server_default=AccountStatus.ACTIVE.value,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
