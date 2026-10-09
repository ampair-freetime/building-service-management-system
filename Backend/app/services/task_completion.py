"""Complete a task and its report in one database transaction."""

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import ImageType, RequestAction, RequestStatus, RequestType
from app.models.image import Image
from app.models.service_request import RequestHistory, ServiceRequest
from app.services.images import prepare_guest_image
from app.services.object_storage import ObjectStorage

logger = logging.getLogger(__name__)


class CompletionNotFoundError(LookupError):
    pass


class CompletionNotOwnedError(PermissionError):
    pass


class CompletionConflictError(RuntimeError):
    pass


async def complete_task_with_report(
    session: AsyncSession,
    *,
    request_id: UUID,
    request_type: RequestType,
    staff_id: UUID,
    note: str,
    uploads: list[UploadFile],
    storage: ObjectStorage | None,
) -> ServiceRequest:
    note = note.strip()
    if not 1 <= len(note) <= 2000:
        raise ValueError("รายงานต้องมีความยาว 1–2,000 ตัวอักษร")
    if len(uploads) > settings.max_guest_images:
        raise ValueError(f"แนบรูปได้ไม่เกิน {settings.max_guest_images} รูป")
    if uploads and storage is None:
        raise ValueError("ระบบจัดเก็บรูปภาพยังไม่พร้อมใช้งาน")
    stored_keys = []
    committed = False
    try:
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
            raise CompletionNotFoundError("ไม่พบงานนี้")
        if task.assigned_staff_id != staff_id:
            raise CompletionNotOwnedError("เฉพาะผู้รับผิดชอบงานเท่านั้นที่ปิดงานได้")
        if task.status != RequestStatus.IN_PROGRESS:
            raise CompletionConflictError("ต้องเริ่มดำเนินการก่อนปิดงาน")
        processed = [await prepare_guest_image(upload) for upload in uploads]
        for index, photo in enumerate(processed):
            image_id = uuid4()
            key = f"{request_type.value}/{request_id}/completion/{image_id}.webp"
            # Include the attempted key: a failed PUT may have reached storage.
            stored_keys.append(key)
            stored = await storage.put(
                object_key=key, data=photo.data, content_type=photo.content_type
            )
            session.add(
                Image(
                    id=image_id,
                    request_id=request_id,
                    object_key=stored.object_key,
                    storage_provider="r2",
                    bucket_name=stored.bucket_name,
                    etag=stored.etag,
                    content_type=photo.content_type,
                    size_bytes=len(photo.data),
                    width=photo.width,
                    height=photo.height,
                    sort_order=index,
                    image_type=ImageType.AFTER,
                    uploaded_by_staff_id=staff_id,
                )
            )
        task.status = RequestStatus.COMPLETED
        task.completed_at = datetime.now(UTC)
        for action, old_status, text in (
            (RequestAction.COMPLETED, RequestStatus.IN_PROGRESS, "ปิดงานพร้อมรายงาน"),
            (RequestAction.COMPLETION_NOTE_ADDED, RequestStatus.COMPLETED, note),
        ):
            session.add(
                RequestHistory(
                    request_id=request_id,
                    action=action,
                    performed_by=staff_id,
                    target_staff_id=staff_id,
                    old_status=old_status,
                    new_status=RequestStatus.COMPLETED,
                    note=text,
                )
            )
        await session.commit()
        committed = True
        return task
    finally:
        if not committed:
            try:
                await session.rollback()
            finally:
                for key in stored_keys:
                    try:
                        await storage.delete(key)
                    except Exception:
                        logger.exception("Failed to clean up completion image %s", key)


async def completion_report_ids(session: AsyncSession, request_ids: list[UUID]) -> set[UUID]:
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
