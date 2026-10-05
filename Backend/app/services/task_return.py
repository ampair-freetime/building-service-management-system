"""คืนงานทำความสะอาด/งานซ่อมที่ staff รับไว้ กลับเข้าคิวกลางให้คนอื่นรับต่อได้."""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RequestAction, RequestStatus, RequestType
from app.models.service_request import RequestHistory, ServiceRequest

# คืนได้เฉพาะงานที่ยังเปิดอยู่และมีผู้รับผิดชอบ งานที่ปิดแล้วหรือยังไม่มีคนรับคืนไม่ได้
RETURNABLE_STATUSES = (
    RequestStatus.ASSIGNED,
    RequestStatus.RECEIVED,
    RequestStatus.IN_PROGRESS,
)


class TaskNotFoundError(LookupError):
    """ไม่พบงานประเภทนี้."""


class TaskNotOwnedError(PermissionError):
    """งานนี้ไม่ได้อยู่ในความรับผิดชอบของ staff ที่ขอคืน."""


class TaskNotReturnableError(RuntimeError):
    """สถานะงานไม่อนุญาตให้คืน หรือถูกเปลี่ยนไปก่อนหน้าพอดี."""


def _history_note(reason: str, note: str | None) -> str:
    return f"{reason} — {note}" if note else reason


async def return_task_to_pool(
    session: AsyncSession,
    *,
    request_id: UUID,
    request_type: RequestType,
    staff_id: UUID,
    reason: str,
    note: str | None = None,
) -> ServiceRequest:
    """ปลด staff ออกจากงาน ตั้งสถานะกลับเป็น waiting และบันทึกประวัติ RETURNED."""
    # Lock แถวงานไว้ก่อน กันการคืนงานชนกับการเปลี่ยนสถานะ/รับงานในจังหวะเดียวกัน
    task = await session.scalar(
        select(ServiceRequest)
        .where(
            ServiceRequest.id == request_id,
            ServiceRequest.request_type == request_type,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if task is None:
        raise TaskNotFoundError(f"{request_type.value.capitalize()} task not found")
    if task.assigned_staff_id != staff_id:
        await session.rollback()
        raise TaskNotOwnedError("This task is not assigned to you")
    old_status = task.status
    if old_status not in RETURNABLE_STATUSES:
        # อ่านค่าไว้ก่อน rollback เพราะ rollback ทำให้ attribute ของ task หมดอายุ
        await session.rollback()
        raise TaskNotReturnableError(f"Cannot return a task with status {old_status.value}")

    # เงื่อนไขซ้ำใน WHERE: ถ้ามีคำสั่งอื่นเปลี่ยนงานไปก่อน (เช่นบน DB ที่ไม่มี row lock)
    # rowcount จะเป็น 0 และเราจะไม่เขียนทับ
    result = await session.execute(
        update(ServiceRequest)
        .where(
            ServiceRequest.id == request_id,
            ServiceRequest.assigned_staff_id == staff_id,
            ServiceRequest.status.in_(RETURNABLE_STATUSES),
        )
        .values(assigned_staff_id=None, status=RequestStatus.WAITING)
    )
    if result.rowcount != 1:
        await session.rollback()
        raise TaskNotReturnableError("Task changed before it could be returned")

    session.add(
        RequestHistory(
            request_id=request_id,
            action=RequestAction.RETURNED,
            # Work Overview นับจำนวนงานที่คืนจาก performed_by
            performed_by=staff_id,
            # คนที่ถูกปลดออกจากงาน
            target_staff_id=staff_id,
            old_status=old_status,
            new_status=RequestStatus.WAITING,
            note=_history_note(reason, note),
        )
    )
    await session.commit()
    await session.refresh(task)
    return task
