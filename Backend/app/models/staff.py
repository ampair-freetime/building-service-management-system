"""SQLAlchemy model สำหรับบัญชีพนักงาน."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AccountStatus, StaffRole

if TYPE_CHECKING:
    from app.models.image import Image
    from app.models.lost_found import LostClaim, LostItem, LostItemHistory
    from app.models.notification import Notification
    from app.models.service_request import RequestHistory, ServiceRequest


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

    assigned_service_requests: Mapped[list["ServiceRequest"]] = relationship(
        back_populates="assigned_staff",
        foreign_keys="ServiceRequest.assigned_staff_id",
    )
    performed_request_histories: Mapped[list["RequestHistory"]] = relationship(
        back_populates="performed_by_staff",
        foreign_keys="RequestHistory.performed_by",
    )
    targeted_request_histories: Mapped[list["RequestHistory"]] = relationship(
        back_populates="target_staff",
        foreign_keys="RequestHistory.target_staff_id",
    )
    reviewed_lost_items: Mapped[list["LostItem"]] = relationship(
        back_populates="reviewer",
        foreign_keys="LostItem.reviewed_by",
    )
    lost_item_history_entries: Mapped[list["LostItemHistory"]] = relationship(
        back_populates="staff",
        foreign_keys="LostItemHistory.staff_id",
    )
    reviewed_lost_claims: Mapped[list["LostClaim"]] = relationship(
        back_populates="reviewer",
        foreign_keys="LostClaim.reviewed_by",
    )
    uploaded_images: Mapped[list["Image"]] = relationship(
        back_populates="uploader",
        foreign_keys="Image.uploaded_by_staff_id",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="staff"
    )
