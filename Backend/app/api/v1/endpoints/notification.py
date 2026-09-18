"""Endpoints สำหรับ Staff notifications."""

from uuid import UUID
from fastapi import APIRouter
from fastapi import APIRouter, HTTPException

from app.api.dependencies import CurrentStaff, DbSession
from app.schemas.notification import NotificationResponse
from app.services.notification import (
    list_staff_notifications,
    mark_notification_as_read,
)

router = APIRouter()


@router.get("", response_model=list[NotificationResponse])
async def read_notifications(
    session: DbSession,
    current_staff: CurrentStaff,
) -> list[NotificationResponse]:
    """ดึง notifications ของ staff ที่กำลัง login อยู่."""
    return await list_staff_notifications(
        session,
        current_staff.id,
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
async def read_notification(
    notification_id: UUID,
    session: DbSession,
    current_staff: CurrentStaff,
) -> NotificationResponse:
    """Mark notification ของ staff ปัจจุบันเป็น read."""

    notification = await mark_notification_as_read(
        session,
        notification_id=notification_id,
        staff_id=current_staff.id,
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    return notification