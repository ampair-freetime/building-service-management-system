"""SQLAlchemy model สำหรับสถานที่และ QR token."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.lost_found import LostItem
    from app.models.service_request import ServiceRequest


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    floor: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # ข้อความอธิบายพื้นที่ เช่น "ห้อง 101" หรือ "ห้องน้ำหญิง" ใช้แสดงผลตรงๆ ไม่ประกอบคำนำหน้าเพิ่ม
    area: Mapped[str] = mapped_column(String(100))
    qr_token: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    service_requests: Mapped[list["ServiceRequest"]] = relationship(
        back_populates="location"
    )
    lost_items: Mapped[list["LostItem"]] = relationship(
        back_populates="location"
    )
