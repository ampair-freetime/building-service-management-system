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
    building: Mapped[str] = mapped_column(String(100))
    floor: Mapped[str | None] = mapped_column(String(30), nullable=True)
    room: Mapped[str | None] = mapped_column(String(100), nullable=True)
    area_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    qr_token: Mapped[str] = mapped_column(String(255), unique=True)
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
