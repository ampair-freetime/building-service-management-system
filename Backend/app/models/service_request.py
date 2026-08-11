"""Models สำหรับหมวดงาน คำร้องบริการ และประวัติการดำเนินงาน."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import PriorityLevel, RequestAction, RequestStatus, RequestType


class ServiceCategory(Base):
    __tablename__ = "service_categories"
    __table_args__ = (
        UniqueConstraint("request_type", "category_name", name="uq_service_category_type_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_type: Mapped[RequestType] = mapped_column(
        SqlEnum(
            RequestType,
            name="request_type",
            values_callable=lambda values: [value.value for value in values],
        )
    )
    category_name: Mapped[str] = mapped_column(String(150))
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ServiceRequest(Base):
    __tablename__ = "service_requests"
    __table_args__ = (
        Index("ix_service_requests_status_created_at", "status", "created_at"),
        Index("ix_service_requests_assigned_staff_status", "assigned_staff_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    request_code: Mapped[str] = mapped_column(String(30), unique=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("service_categories.id"))
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    location_detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
    priority: Mapped[PriorityLevel] = mapped_column(
        SqlEnum(
            PriorityLevel,
            name="priority_level",
            values_callable=lambda values: [value.value for value in values],
        ),
        default=PriorityLevel.NORMAL,
        server_default=PriorityLevel.NORMAL.value,
    )
    status: Mapped[RequestStatus] = mapped_column(
        SqlEnum(
            RequestStatus,
            name="request_status",
            values_callable=lambda values: [value.value for value in values],
        ),
        default=RequestStatus.WAITING,
        server_default=RequestStatus.WAITING.value,
        index=True,
    )
    reporter_email: Mapped[str] = mapped_column(String(255), index=True)
    assigned_staff_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("staff.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class RequestHistory(Base):
    __tablename__ = "request_history"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(ForeignKey("service_requests.id"))
    action: Mapped[RequestAction] = mapped_column(
        SqlEnum(
            RequestAction,
            name="request_action",
            values_callable=lambda values: [value.value for value in values],
        )
    )
    performed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("staff.id"), nullable=True
    )
    target_staff_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("staff.id"), nullable=True
    )
    old_status: Mapped[RequestStatus | None] = mapped_column(
        SqlEnum(
            RequestStatus,
            name="request_status",
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=True,
    )
    new_status: Mapped[RequestStatus | None] = mapped_column(
        SqlEnum(
            RequestStatus,
            name="request_status",
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
