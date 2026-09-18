"""Business logic สำหรับ Cleaning Staff."""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RequestAction, RequestStatus, RequestType
from app.models.service_request import RequestHistory, ServiceRequest


class CleaningTaskNotFoundError(LookupError):
    """ไม่พบ cleaning task."""


class CleaningTaskAlreadyAssignedError(RuntimeError):
    """Cleaning task ถูก cleaner คนอื่นรับไปแล้ว."""


async def accept_cleaning_task(
    session: AsyncSession,
    *,
    request_id: UUID,
    staff_id: UUID,
) -> ServiceRequest:
    """ให้ cleaner รับ cleaning task ที่ยังว่างอยู่."""

    # ตรวจว่ามี cleaning task นี้จริงหรือไม่
    existing_task = await session.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.request_type == RequestType.CLEANING,
        )
    )

    if existing_task is None:
        raise CleaningTaskNotFoundError("Cleaning task not found")

    # Atomic update:
    # จะ update ได้ก็ต่อเมื่องานยัง WAITING และยังไม่มีคนรับ
    result = await session.execute(
        update(ServiceRequest)
        .where(
            ServiceRequest.id == request_id,
            ServiceRequest.request_type == RequestType.CLEANING,
            ServiceRequest.status == RequestStatus.WAITING,
            ServiceRequest.assigned_staff_id.is_(None),
        )
        .values(
            assigned_staff_id=staff_id,
            status=RequestStatus.ASSIGNED,
        )
    )

    if result.rowcount != 1:
        await session.rollback()
        raise CleaningTaskAlreadyAssignedError(
            "Cleaning task has already been assigned"
        )

    session.add(
        RequestHistory(
            request_id=request_id,
            action=RequestAction.ACCEPTED,
            performed_by=staff_id,
            target_staff_id=staff_id,
            old_status=RequestStatus.WAITING,
            new_status=RequestStatus.ASSIGNED,
            note="Cleaning task accepted",
        )
    )

    await session.commit()

    service_request = await session.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id
        )
    )

    if service_request is None:
        raise CleaningTaskNotFoundError("Cleaning task not found")

    return service_request