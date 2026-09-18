"""Business logic สำหรับ Staff notifications."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AccountStatus, StaffRole
from app.models.notification import Notification
from app.models.staff import Staff


async def list_staff_notifications(
    session: AsyncSession,
    staff_id: UUID,
) -> list[Notification]:
    """ดึง notification ของ staff คนปัจจุบัน เรียงจากใหม่ไปเก่า."""

    result = await session.scalars(
        select(Notification)
        .where(Notification.staff_id == staff_id)
        .order_by(Notification.created_at.desc())
    )

    return list(result.all())


async def create_cleaning_request_notifications(
    session: AsyncSession,
    *,
    request_id: UUID,
    request_code: str,
    request_title: str,
) -> None:
    """สร้าง notification ให้ housekeeper ที่ active ทุกคน."""

    result = await session.scalars(
        select(Staff).where(
            Staff.role == StaffRole.HOUSEKEEPER,
            Staff.status == AccountStatus.ACTIVE,
        )
    )

    housekeepers = result.all()

    for housekeeper in housekeepers:
        session.add(
            Notification(
                staff_id=housekeeper.id,
                request_id=request_id,
                title="New cleaning request",
                message=f"{request_code}: {request_title}",
                is_read=False,
            )
        )


async def mark_notification_as_read(
    session: AsyncSession,
    *,
    notification_id: UUID,
    staff_id: UUID,
) -> Notification | None:
    """Mark notification เป็น read เฉพาะ notification ของ staff คนปัจจุบัน."""

    notification = await session.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.staff_id == staff_id,
        )
    )

    if notification is None:
        return None

    notification.is_read = True

    await session.commit()
    await session.refresh(notification)

    return notification
