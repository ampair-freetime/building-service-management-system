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


class InvalidCleaningStatusTransitionError(RuntimeError):
    """เปลี่ยนสถานะ cleaning task ไม่ถูกลำดับ."""


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


async def update_cleaning_task_status(
    session: AsyncSession,
    *,
    request_id: UUID,
    staff_id: UUID,
    new_status: RequestStatus,
) -> ServiceRequest:
    """อัปเดตสถานะ cleaning task ตามลำดับที่กำหนด."""

    service_request = await session.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.request_type == RequestType.CLEANING,
        )
    )

    if service_request is None:
        raise CleaningTaskNotFoundError("Cleaning task not found")

    # Cleaner เปลี่ยนสถานะได้เฉพาะงานที่ตัวเองรับไว้
    if service_request.assigned_staff_id != staff_id:
        raise CleaningTaskAlreadyAssignedError(
            "Cleaning task is assigned to another cleaner"
        )

    valid_transitions = {
        RequestStatus.ASSIGNED: RequestStatus.RECEIVED,
        RequestStatus.RECEIVED: RequestStatus.IN_PROGRESS,
        RequestStatus.IN_PROGRESS: RequestStatus.COMPLETED,
    }

    expected_status = valid_transitions.get(service_request.status)

    if expected_status != new_status:
        raise InvalidCleaningStatusTransitionError(
            f"Cannot change cleaning task status "
            f"from {service_request.status.value} to {new_status.value}"
        )

    old_status = service_request.status
    service_request.status = new_status

    session.add(
        RequestHistory(
            request_id=service_request.id,
            action=(
                RequestAction.COMPLETED
                if new_status == RequestStatus.COMPLETED
                else RequestAction.STATUS_CHANGED
            ),
            performed_by=staff_id,
            target_staff_id=staff_id,
            old_status=old_status,
            new_status=new_status,
            note=f"Cleaning task status changed to {new_status.value}",
        )
    )

    await session.commit()
    await session.refresh(service_request)

    return service_request