from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.enums import ImageType, RequestAction, RequestStatus, RequestType
from app.models.image import Image
from app.models.service_request import RequestHistory, ServiceRequest
from app.services.object_storage import ObjectStorage
from app.services.photo_attachments import stage_photos


class TaskNotFoundError(LookupError):
    """ไม่พบงานประเภทนี้ หรือ staff คนนี้ไม่มีสิทธิ์เห็นงานนั้น."""


class TaskNotOwnedError(PermissionError):
    """งานนี้ไม่ได้อยู่ในความรับผิดชอบของ staff ที่สั่ง."""


class TaskConflictError(RuntimeError):
    """สถานะงานตอนนี้ไม่อนุญาตให้ทำคำสั่งนี้ (ถูกรับไปแล้ว, ข้ามขั้น, ยังไม่เสร็จ ฯลฯ)."""


@dataclass(frozen=True)
class TaskKind:
    request_type: RequestType
    noun: str  # ใช้ขึ้นต้นข้อความ error และ note ใน history
    worker: str
    not_found_message: str
    # True = เห็นเฉพาะงานว่างกับงานของตัวเอง; False = เห็นงานทุกงานของประเภทนี้
    owner_only_visibility: bool


TASK_KINDS = {
    RequestType.CLEANING: TaskKind(
        request_type=RequestType.CLEANING,
        noun="Cleaning task",
        worker="cleaner",
        not_found_message="Cleaning task not found",
        owner_only_visibility=True,
    ),
    RequestType.REPAIR: TaskKind(
        request_type=RequestType.REPAIR,
        noun="Repair task",
        worker="technician",
        not_found_message="Repair request not found",
        # ช่างเห็นเฉพาะงานว่างกับงานของตัวเอง ไม่เห็นงานและอีเมลผู้แจ้งของช่างคนอื่น
        owner_only_visibility=True,
    ),
}

# ขั้นถัดไปที่ staff เลื่อนเองได้ (completed ต้องผ่าน complete_task_with_report เท่านั้น)
NEXT_STATUS = {
    RequestStatus.ASSIGNED: RequestStatus.RECEIVED,
    RequestStatus.RECEIVED: RequestStatus.IN_PROGRESS,
}

# คืนได้เฉพาะงานที่ยังเปิดอยู่และมีผู้รับผิดชอบ งานที่ปิดแล้วหรือยังไม่มีคนรับคืนไม่ได้
RETURNABLE_STATUSES = (
    RequestStatus.ASSIGNED,
    RequestStatus.RECEIVED,
    RequestStatus.IN_PROGRESS,
)


# ---------------------------------------------------------------- อ่านงาน


def _visible_to(kind: TaskKind, staff_id: UUID):
    if not kind.owner_only_visibility:
        return ServiceRequest.request_type == kind.request_type
    return and_(
        ServiceRequest.request_type == kind.request_type,
        or_(
            and_(
                ServiceRequest.status == RequestStatus.WAITING,
                ServiceRequest.assigned_staff_id.is_(None),
            ),
            ServiceRequest.assigned_staff_id == staff_id,
        ),
    )


async def list_tasks(
    session: AsyncSession, *, request_type: RequestType, staff_id: UUID
) -> list[ServiceRequest]:
    """งานสำหรับ dashboard เรียงรายการล่าสุดก่อน พร้อมสถานที่ในคำสั่งเดียว."""
    kind = TASK_KINDS[request_type]
    tasks = await session.scalars(
        select(ServiceRequest)
        .options(selectinload(ServiceRequest.location))
        .where(_visible_to(kind, staff_id))
        .order_by(ServiceRequest.created_at.desc(), ServiceRequest.id.desc())
    )
    return list(tasks)


async def get_task_detail(
    session: AsyncSession, *, request_type: RequestType, request_id: UUID, staff_id: UUID
) -> ServiceRequest:
    """รายละเอียดงานพร้อมรูป; งานที่มองไม่เห็นตอบเหมือนไม่พบ เพื่อไม่เปิดเผยอีเมลผู้แจ้ง."""
    kind = TASK_KINDS[request_type]
    task = await session.scalar(
        select(ServiceRequest)
        .options(
            selectinload(ServiceRequest.location),
            selectinload(ServiceRequest.images),
        )
        .where(ServiceRequest.id == request_id, _visible_to(kind, staff_id))
    )
    if task is None:
        raise TaskNotFoundError(kind.not_found_message)
    return task


async def get_work_history(
    session: AsyncSession, *, request_type: RequestType, request_id: UUID, staff_id: UUID
) -> list[RequestHistory]:
    """ประวัติงาน ดูได้เฉพาะผู้รับผิดชอบงาน."""
    await _load_owned(session, TASK_KINDS[request_type], request_id, staff_id)
    history = await session.scalars(
        select(RequestHistory)
        .where(RequestHistory.request_id == request_id)
        .order_by(RequestHistory.created_at.asc(), RequestHistory.id.asc())
    )
    return list(history)


async def completion_report_ids(session: AsyncSession, request_ids: list[UUID]) -> set[UUID]:
    """id ของงานที่มีรายงานปิดงานแล้ว (ใช้ทำป้าย "มีรายงาน" ในรายการงาน)."""
    if not request_ids:
        return set()
    return set(
        await session.scalars(
            select(RequestHistory.request_id).where(
                RequestHistory.request_id.in_(request_ids),
                RequestHistory.action == RequestAction.COMPLETION_NOTE_ADDED,
            )
        )
    )


# ---------------------------------------------------------------- เปลี่ยนสถานะ


async def accept_task(
    session: AsyncSession, *, request_type: RequestType, request_id: UUID, staff_id: UUID
) -> ServiceRequest:
    """รับงานที่ยังว่าง; ถ้ามีคนรับตัดหน้าไปก่อนจะได้ TaskConflictError."""
    kind = TASK_KINDS[request_type]
    await _load(session, kind, request_id)

    # Atomic update: สำเร็จก็ต่อเมื่องานยัง WAITING และยังไม่มีคนรับ ณ ตอนที่เขียน
    result = await session.execute(
        update(ServiceRequest)
        .where(
            ServiceRequest.id == request_id,
            ServiceRequest.request_type == request_type,
            ServiceRequest.status == RequestStatus.WAITING,
            ServiceRequest.assigned_staff_id.is_(None),
        )
        .values(assigned_staff_id=staff_id, status=RequestStatus.ASSIGNED)
    )
    if result.rowcount != 1:
        await session.rollback()
        raise TaskConflictError(f"{kind.noun} has already been assigned")

    _record(
        session,
        request_id,
        RequestAction.ACCEPTED,
        staff_id,
        RequestStatus.WAITING,
        RequestStatus.ASSIGNED,
        f"{kind.noun} accepted",
    )
    await session.commit()
    return await _load(session, kind, request_id, refresh=True)


async def advance_task_status(
    session: AsyncSession,
    *,
    request_type: RequestType,
    request_id: UUID,
    staff_id: UUID,
    new_status: RequestStatus,
) -> ServiceRequest:
    """เลื่อนสถานะทีละขั้นตาม NEXT_STATUS (assigned → received → in_progress)."""
    kind = TASK_KINDS[request_type]
    task = await _load_owned(session, kind, request_id, staff_id, lock=True)
    old_status = task.status
    if NEXT_STATUS.get(old_status) != new_status:
        raise TaskConflictError(
            f"Cannot change {kind.noun.lower()} status "
            f"from {old_status.value} to {new_status.value}"
        )
    task.status = new_status
    _record(
        session,
        request_id,
        RequestAction.STATUS_CHANGED,
        staff_id,
        old_status,
        new_status,
        f"{kind.noun} status changed to {new_status.value}",
    )
    await session.commit()
    await session.refresh(task)
    return task


async def complete_task_with_report(
    session: AsyncSession,
    *,
    request_type: RequestType,
    request_id: UUID,
    staff_id: UUID,
    note: str,
    uploads: list[UploadFile],
    storage: ObjectStorage | None,
) -> ServiceRequest:
    """ปิดงานพร้อมรายงานและรูปหลังทำ ใน transaction เดียว."""
    kind = TASK_KINDS[request_type]
    note = note.strip()
    if not 1 <= len(note) <= 2000:
        raise ValueError("รายงานต้องมีความยาว 1–2,000 ตัวอักษร")
    if len(uploads) > settings.max_guest_images:
        raise ValueError(f"แนบรูปได้ไม่เกิน {settings.max_guest_images} รูป")
    if uploads and storage is None:
        raise ValueError("ระบบจัดเก็บรูปภาพยังไม่พร้อมใช้งาน")

    # ตรวจแบบไม่ lock ก่อน ถ้าไม่ผ่านจะได้ไม่เสียเวลาอัปรูป
    _ensure_completable(await _load(session, kind, request_id), staff_id)

    # อัปรูปขึ้น R2 ก่อน lock แถวงาน: การอัปโหลดใช้เวลาเป็นวินาที ถ้าถือ row lock ไว้
    # ระหว่างนั้น ทุก request ที่แตะงานนี้ต้องรอไปด้วย
    async with await stage_photos(
        storage, uploads, key_prefix=f"{request_type.value}/{request_id}/completion"
    ) as photos:
        try:
            # ตรวจซ้ำหลัง lock เพราะระหว่างอัปรูปอาจมีคนคืนงานหรือปิดงานไปแล้ว
            task = await _load(session, kind, request_id, lock=True)
            _ensure_completable(task, staff_id)
            session.add_all(
                photos.image_rows(
                    request_id=request_id,
                    image_type=ImageType.AFTER,
                    uploaded_by_staff_id=staff_id,
                )
            )
            task.status = RequestStatus.COMPLETED
            task.completed_at = datetime.now(UTC)
            _record(
                session,
                request_id,
                RequestAction.COMPLETED,
                staff_id,
                RequestStatus.IN_PROGRESS,
                RequestStatus.COMPLETED,
                "ปิดงานพร้อมรายงาน",
            )
            _record(
                session,
                request_id,
                RequestAction.COMPLETION_NOTE_ADDED,
                staff_id,
                RequestStatus.COMPLETED,
                RequestStatus.COMPLETED,
                note,
            )
            await session.commit()
        except BaseException:
            await session.rollback()
            raise
        photos.keep()
    return task


async def return_task_to_pool(
    session: AsyncSession,
    *,
    request_type: RequestType,
    request_id: UUID,
    staff_id: UUID,
    reason: str,
    note: str | None = None,
) -> ServiceRequest:
    """ปลด staff ออกจากงาน ตั้งสถานะกลับเป็น waiting และบันทึกประวัติ RETURNED."""
    kind = TASK_KINDS[request_type]
    # Lock แถวงานไว้ก่อน กันการคืนงานชนกับการเปลี่ยนสถานะ/รับงานในจังหวะเดียวกัน
    task = await _load(session, kind, request_id, lock=True)
    if task.assigned_staff_id != staff_id:
        await session.rollback()
        raise TaskNotOwnedError("This task is not assigned to you")
    old_status = task.status
    if old_status not in RETURNABLE_STATUSES:
        # อ่านค่าไว้ก่อน rollback เพราะ rollback ทำให้ attribute ของ task หมดอายุ
        await session.rollback()
        raise TaskConflictError(f"Cannot return a task with status {old_status.value}")

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
        raise TaskConflictError("Task changed before it could be returned")

    _record(
        session,
        request_id,
        RequestAction.RETURNED,
        staff_id,
        old_status,
        RequestStatus.WAITING,
        f"{reason} — {note}" if note else reason,
    )
    await session.commit()
    await session.refresh(task)
    return task


# ------------------------------------------- รายงานแบบเดิม (เพิ่มหลังปิดงานแล้ว)
# หน้า dashboard รุ่นเก่ายังเรียกสองเส้นนี้ ส่วนการปิดงานปกติใช้ complete_task_with_report


async def add_completion_note(
    session: AsyncSession,
    *,
    request_type: RequestType,
    request_id: UUID,
    staff_id: UUID,
    note: str,
) -> RequestHistory:
    """บันทึกรายงานเพิ่มเติมให้งานที่เสร็จแล้ว."""
    kind = TASK_KINDS[request_type]
    task = await _load_owned(session, kind, request_id, staff_id)
    if task.status != RequestStatus.COMPLETED:
        raise TaskConflictError(f"{kind.noun} must be completed before adding a note")
    cleaned_note = note.strip()
    if not cleaned_note:
        raise ValueError("Completion note must not be empty")

    history = _record(
        session,
        request_id,
        RequestAction.COMPLETION_NOTE_ADDED,
        staff_id,
        RequestStatus.COMPLETED,
        RequestStatus.COMPLETED,
        cleaned_note,
    )
    await session.commit()
    await session.refresh(history)
    return history


async def upload_completion_photos(
    session: AsyncSession,
    *,
    request_type: RequestType,
    request_id: UUID,
    staff_id: UUID,
    uploads: list[UploadFile],
    storage: ObjectStorage,
) -> list[Image]:
    """แนบรูปหลังทำให้งานที่เสร็จแล้ว."""
    kind = TASK_KINDS[request_type]
    task = await _load_owned(session, kind, request_id, staff_id)
    if task.status != RequestStatus.COMPLETED:
        raise TaskConflictError(
            f"{kind.noun} must be completed before uploading completion photos"
        )
    if not uploads:
        raise ValueError("At least one completion photo is required")

    async with await stage_photos(
        storage, uploads, key_prefix=f"{request_type.value}/{request_id}/completion"
    ) as photos:
        images = photos.image_rows(
            request_id=request_id,
            image_type=ImageType.AFTER,
            uploaded_by_staff_id=staff_id,
        )
        try:
            session.add_all(images)
            await session.flush()
            # เอา created_at ที่ DB สร้างให้กลับมาใช้ใน response
            for image in images:
                await session.refresh(image)
            await session.commit()
        except BaseException:
            await session.rollback()
            raise
        photos.keep()
    return images


# ---------------------------------------------------------------- ตัวช่วยภายใน


async def _load(
    session: AsyncSession,
    kind: TaskKind,
    request_id: UUID,
    *,
    lock: bool = False,
    refresh: bool = False,
) -> ServiceRequest:
    statement = select(ServiceRequest).where(
        ServiceRequest.id == request_id,
        ServiceRequest.request_type == kind.request_type,
    )
    if lock:
        statement = statement.with_for_update()
    if lock or refresh:
        # อ่านค่าล่าสุดจาก DB ไม่ใช้ค่าเก่าที่ session จำไว้
        statement = statement.execution_options(populate_existing=True)
    task = await session.scalar(statement)
    if task is None:
        raise TaskNotFoundError(kind.not_found_message)
    return task


async def _load_owned(
    session: AsyncSession,
    kind: TaskKind,
    request_id: UUID,
    staff_id: UUID,
    *,
    lock: bool = False,
) -> ServiceRequest:
    task = await _load(session, kind, request_id, lock=lock)
    if task.assigned_staff_id != staff_id:
        raise TaskNotOwnedError(f"{kind.noun} is assigned to another {kind.worker}")
    return task


def _ensure_completable(task: ServiceRequest, staff_id: UUID) -> None:
    # ข้อความภาษาไทยสองข้อนี้หน้า dashboard แสดงให้ staff เห็นตรง ๆ
    if task.assigned_staff_id != staff_id:
        raise TaskNotOwnedError("เฉพาะผู้รับผิดชอบงานเท่านั้นที่ปิดงานได้")
    if task.status != RequestStatus.IN_PROGRESS:
        raise TaskConflictError("ต้องเริ่มดำเนินการก่อนปิดงาน")


def _record(
    session: AsyncSession,
    request_id: UUID,
    action: RequestAction,
    staff_id: UUID,
    old_status: RequestStatus | None,
    new_status: RequestStatus,
    note: str,
) -> RequestHistory:
    """เพิ่มแถวประวัติงาน; staff ที่ทำคือคนที่รับผิดชอบงานเสมอในโมดูลนี้.

    Work Overview นับงานที่คืนจาก performed_by และงานที่ปิดจาก target_staff_id
    """
    history = RequestHistory(
        request_id=request_id,
        action=action,
        performed_by=staff_id,
        target_staff_id=staff_id,
        old_status=old_status,
        new_status=new_status,
        note=note,
    )
    session.add(history)
    return history
