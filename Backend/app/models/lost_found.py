"""Models สำหรับของหาย ของที่พบ ประวัติ และคำขอรับคืน."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ClaimStatus, LostStatus, LostType


class LostItem(Base):
    __tablename__ = "lost_items"
    __table_args__ = (Index("ix_lost_items_report_type_status", "report_type", "status"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    item_code: Mapped[str] = mapped_column(String(30), unique=True)
    report_type: Mapped[LostType] = mapped_column(
        SqlEnum(
            LostType,
            name="lost_type",
            values_callable=lambda values: [value.value for value in values],
        ),
        index=True,
    )
    item_category: Mapped[str] = mapped_column(String(100))
    item_name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    location_detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custody_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    private_verification_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    reporter_email: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[LostStatus] = mapped_column(
        SqlEnum(
            LostStatus,
            name="lost_status",
            values_callable=lambda values: [value.value for value in values],
        ),
        default=LostStatus.PENDING,
        server_default=LostStatus.PENDING.value,
        index=True,
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(ForeignKey("staff.id"), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # ช่องสำหรับ retention policy ในอนาคต รอบนี้ยังไม่มี job เปลี่ยนค่าอัตโนมัติ
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LostItemHistory(Base):
    __tablename__ = "lost_item_history"
    __table_args__ = (
        Index("ix_lost_item_history_item_created_at", "lost_item_id", "created_at"),
        Index("ix_lost_item_history_staff_created_at", "staff_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lost_item_id: Mapped[UUID] = mapped_column(ForeignKey("lost_items.id"))
    staff_id: Mapped[UUID | None] = mapped_column(ForeignKey("staff.id"), nullable=True)
    old_status: Mapped[LostStatus | None] = mapped_column(
        SqlEnum(
            LostStatus,
            name="lost_status",
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=True,
    )
    new_status: Mapped[LostStatus] = mapped_column(
        SqlEnum(
            LostStatus,
            name="lost_status",
            values_callable=lambda values: [value.value for value in values],
        )
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LostClaim(Base):
    __tablename__ = "lost_claims"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    found_item_id: Mapped[UUID] = mapped_column(ForeignKey("lost_items.id"), index=True)
    claimant_name: Mapped[str] = mapped_column(String(150))
    claimant_email: Mapped[str] = mapped_column(String(255), index=True)
    proof_detail: Mapped[str] = mapped_column(Text)
    status: Mapped[ClaimStatus] = mapped_column(
        SqlEnum(
            ClaimStatus,
            name="claim_status",
            values_callable=lambda values: [value.value for value in values],
        ),
        default=ClaimStatus.PENDING,
        server_default=ClaimStatus.PENDING.value,
        index=True,
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(ForeignKey("staff.id"), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
