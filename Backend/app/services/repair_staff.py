"""Business logic สำหรับ Repair Staff."""
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from uuid import UUID
from app.models.enums import RequestAction, RequestStatus, RequestType
from app.models.service_request import RequestHistory, ServiceRequest


async def list_repair_requests(
    session: AsyncSession,
) -> list[ServiceRequest]:
    """ดึงรายการ repair requests โดยเรียงรายการล่าสุดก่อน."""

    requests = (
        await session.scalars(
            select(ServiceRequest)
            .options(selectinload(ServiceRequest.location))
            .where(ServiceRequest.request_type == RequestType.REPAIR)
            .order_by(
                ServiceRequest.created_at.desc(),
                ServiceRequest.id.desc(),
            )
        )
    ).all()

    return list(requests)


class RepairRequestNotFoundError(LookupError):
    """ไม่พบ repair request ที่ต้องการ."""


class RepairTaskAlreadyAssignedError(RuntimeError):
    """Repair task ถูก technician คนอื่นรับไปแล้ว."""


class InvalidRepairStatusTransitionError(RuntimeError):
    """เปลี่ยนสถานะ repair task ไม่ถูกลำดับ."""


class RepairTaskNotInProgressError(RuntimeError):
    """Repair task ต้องอยู่ในสถานะ in progress ก่อนจึงจะ complete ได้."""


class RepairTaskNotCompletedError(RuntimeError):
    """Repair task ยังไม่เสร็จ จึงเพิ่ม repair note ไม่ได้."""


async def get_repair_request_detail(
    session: AsyncSession,
    request_id: UUID,
) -> ServiceRequest:
    """ดึงรายละเอียด repair request พร้อม location และ images."""

    request = await session.scalar(
        select(ServiceRequest)
        .options(
            selectinload(ServiceRequest.location),
            selectinload(ServiceRequest.images),
        )
        .where(
            ServiceRequest.id == request_id,
            ServiceRequest.request_type == RequestType.REPAIR,
        )
    )

    if request is None:
        raise RepairRequestNotFoundError("Repair request not found")

    return request


async def accept_repair_task(
    session: AsyncSession,
    *,
    request_id: UUID,
    staff_id: UUID,
) -> ServiceRequest:
    """ให้ technician รับ repair task ที่ยังไม่มีผู้รับผิดชอบ."""

    existing_task = await session.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.request_type == RequestType.REPAIR,
        )
    )

    if existing_task is None:
        raise RepairRequestNotFoundError("Repair request not found")

    result = await session.execute(
        update(ServiceRequest)
        .where(
            ServiceRequest.id == request_id,
            ServiceRequest.request_type == RequestType.REPAIR,
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
        raise RepairTaskAlreadyAssignedError(
            "Repair task has already been assigned"
        )

    session.add(
        RequestHistory(
            request_id=request_id,
            action=RequestAction.ACCEPTED,
            performed_by=staff_id,
            target_staff_id=staff_id,
            old_status=RequestStatus.WAITING,
            new_status=RequestStatus.ASSIGNED,
            note="Repair task accepted",
        )
    )

    await session.commit()

    service_request = await session.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id
        )
    )

    if service_request is None:
        raise RepairRequestNotFoundError("Repair request not found")

    return service_request


async def update_repair_task_status(
    session: AsyncSession,
    *,
    request_id: UUID,
    staff_id: UUID,
    new_status: RequestStatus,
) -> ServiceRequest:
    """อัปเดตสถานะ repair task ตามลำดับที่กำหนด."""

    service_request = await session.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.request_type == RequestType.REPAIR,
        )
    )

    if service_request is None:
        raise RepairRequestNotFoundError("Repair request not found")

    # Technician เปลี่ยนสถานะได้เฉพาะงานที่ตัวเองรับไว้
    if service_request.assigned_staff_id != staff_id:
        raise RepairTaskAlreadyAssignedError(
            "Repair task is assigned to another technician"
        )

    valid_transitions = {
        RequestStatus.ASSIGNED: RequestStatus.RECEIVED,
        RequestStatus.RECEIVED: RequestStatus.IN_PROGRESS,
    }

    expected_status = valid_transitions.get(service_request.status)

    if expected_status != new_status:
        raise InvalidRepairStatusTransitionError(
            f"Cannot change repair task status "
            f"from {service_request.status.value} to {new_status.value}"
        )

    old_status = service_request.status
    service_request.status = new_status

    session.add(
        RequestHistory(
            request_id=service_request.id,
            action=RequestAction.STATUS_CHANGED,
            performed_by=staff_id,
            target_staff_id=staff_id,
            old_status=old_status,
            new_status=new_status,
            note=f"Repair task status changed to {new_status.value}",
        )
    )

    await session.commit()
    await session.refresh(service_request)

    return service_request


async def complete_repair_task(
    session: AsyncSession,
    *,
    request_id: UUID,
    staff_id: UUID,
) -> ServiceRequest:
    """ทำเครื่องหมาย repair task ว่าเสร็จสมบูรณ์."""

    service_request = await session.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.request_type == RequestType.REPAIR,
        )
    )

    if service_request is None:
        raise RepairRequestNotFoundError("Repair request not found")

    # Complete ได้เฉพาะ technician ที่รับงานนี้
    if service_request.assigned_staff_id != staff_id:
        raise RepairTaskAlreadyAssignedError(
            "Repair task is assigned to another technician"
        )

    # ต้องผ่านขั้น IN_PROGRESS ก่อน
    if service_request.status != RequestStatus.IN_PROGRESS:
        raise RepairTaskNotInProgressError(
            "Repair task must be in progress before completion"
        )

    old_status = service_request.status
    service_request.status = RequestStatus.COMPLETED
    service_request.completed_at = datetime.now(UTC)

    session.add(
        RequestHistory(
            request_id=service_request.id,
            action=RequestAction.COMPLETED,
            performed_by=staff_id,
            target_staff_id=staff_id,
            old_status=old_status,
            new_status=RequestStatus.COMPLETED,
            note="Repair task completed",
        )
    )

    await session.commit()
    await session.refresh(service_request)

    return service_request


async def add_repair_completion_note(
    session: AsyncSession,
    *,
    request_id: UUID,
    staff_id: UUID,
    note: str,
) -> RequestHistory:
    """เพิ่ม repair completion note หลังงานเสร็จแล้ว."""

    service_request = await session.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.request_type == RequestType.REPAIR,
        )
    )

    if service_request is None:
        raise RepairRequestNotFoundError("Repair request not found")

    if service_request.assigned_staff_id != staff_id:
        raise RepairTaskAlreadyAssignedError(
            "Repair task is assigned to another technician"
        )

    if service_request.status != RequestStatus.COMPLETED:
        raise RepairTaskNotCompletedError(
            "Repair task must be completed before adding a note"
        )

    cleaned_note = note.strip()

    if not cleaned_note:
        raise ValueError("Repair note must not be empty")

    history = RequestHistory(
        request_id=request_id,
        action=RequestAction.COMPLETION_NOTE_ADDED,
        performed_by=staff_id,
        target_staff_id=staff_id,
        old_status=RequestStatus.COMPLETED,
        new_status=RequestStatus.COMPLETED,
        note=cleaned_note,
    )

    session.add(history)
    await session.commit()
    await session.refresh(history)

    return history


async def get_repair_work_history(
    session: AsyncSession,
    *,
    request_id: UUID,
    staff_id: UUID,
) -> list[RequestHistory]:
    """ดึงประวัติการทำงานของ repair task."""

    service_request = await session.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.request_type == RequestType.REPAIR,
        )
    )

    if service_request is None:
        raise RepairRequestNotFoundError("Repair request not found")

    if service_request.assigned_staff_id != staff_id:
        raise RepairTaskAlreadyAssignedError(
            "Repair task is assigned to another technician"
        )

    history = (
        await session.scalars(
            select(RequestHistory)
            .where(RequestHistory.request_id == request_id)
            .order_by(
                RequestHistory.created_at.asc(),
                RequestHistory.id.asc(),
            )
        )
    ).all()

    return list(history)