"""Model สำหรับ URL รูปภาพของ Service Request หรือ Lost Item."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text, Uuid, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ImageType


class Image(Base):
    __tablename__ = "images"
    __table_args__ = (
        CheckConstraint(
            "(request_id IS NOT NULL AND lost_item_id IS NULL AND image_type IS NOT NULL) "
            "OR (request_id IS NULL AND lost_item_id IS NOT NULL AND image_type IS NULL)",
            name="image_parent_check",
        ),
        Index("ix_images_request_id", "request_id"),
        Index("ix_images_lost_item_id", "lost_item_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("service_requests.id"), nullable=True
    )
    lost_item_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("lost_items.id"), nullable=True
    )
    image_url: Mapped[str] = mapped_column(Text)
    image_type: Mapped[ImageType | None] = mapped_column(
        SqlEnum(
            ImageType,
            name="image_type",
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=True,
    )
    uploaded_by_staff_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("staff.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
