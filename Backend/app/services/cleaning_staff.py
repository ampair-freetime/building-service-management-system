"""Business logic สำหรับ Cleaning Staff."""

from dataclasses import dataclass
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ImageType, RequestAction, RequestStatus, RequestType
from app.models.image import Image
from app.models.service_request import RequestHistory, ServiceRequest
from app.services.images import ProcessedImage, prepare_guest_image
from app.services.object_storage import ObjectStorage, StoredObject


class CleaningTaskNotFoundError(LookupError):
    """ไม่พบ cleaning task."""


class CleaningTaskAlreadyAssignedError(RuntimeError):
    """Cleaning task ถูก cleaner คนอื่นรับไปแล้ว."""


class InvalidCleaningStatusTransitionError(RuntimeError):
    """เปลี่ยนสถานะ cleaning task ไม่ถูกลำดับ."""


class CleaningTaskNotCompletedError(RuntimeError):
    """Cleaning task ยังไม่เสร็จ จึงอัปโหลด completion photo ไม่ได้."""


@dataclass(frozen=True)
class _PreparedCompletionPhoto:
    image_id: UUID
    processed: ProcessedImage
    stored: StoredObject

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


async def upload_completion_photos(
    session: AsyncSession,
    *,
    request_id: UUID,
    staff_id: UUID,
    uploads: list[UploadFile],
    storage: ObjectStorage,
) -> list[Image]:
    """อัปโหลดรูปหลังทำความสะอาดสำหรับงานที่เสร็จแล้ว."""

    service_request = await session.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.request_type == RequestType.CLEANING,
        )
    )

    if service_request is None:
        raise CleaningTaskNotFoundError("Cleaning task not found")

    # อัปโหลดได้เฉพาะ cleaner ที่รับงานนี้
    if service_request.assigned_staff_id != staff_id:
        raise CleaningTaskAlreadyAssignedError(
            "Cleaning task is assigned to another cleaner"
        )

    # Completion photos อัปโหลดได้หลังงานเสร็จเท่านั้น
    if service_request.status != RequestStatus.COMPLETED:
        raise CleaningTaskNotCompletedError(
            "Cleaning task must be completed before uploading completion photos"
        )

    # ต้องมีอย่างน้อย 1 รูป
    if not uploads:
        raise ValueError("At least one completion photo is required")

    # Validate/ประมวลผลรูปทั้งหมดก่อน
    # เพื่อไม่ให้อัปโหลดบางรูปไป R2 แล้วค่อยพบว่ารูปถัดไป invalid
    processed_uploads: list[ProcessedImage] = []

    for upload in uploads:
        processed_uploads.append(
            await prepare_guest_image(upload)
        )

    prepared: list[_PreparedCompletionPhoto] = []
    images: list[Image] = []
    committed = False

    try:
        for processed in processed_uploads:
            image_id = uuid4()

            stored = await storage.put(
                object_key=f"cleaning/{request_id}/completion/{image_id}.webp",
                data=processed.data,
                content_type=processed.content_type,
            )

            prepared.append(
                _PreparedCompletionPhoto(
                    image_id=image_id,
                    processed=processed,
                    stored=stored,
                )
            )

        for item in prepared:
            image = Image(
                id=item.image_id,
                request_id=request_id,
                lost_item_id=None,
                object_key=item.stored.object_key,
                storage_provider="r2",
                bucket_name=item.stored.bucket_name,
                content_type=item.processed.content_type,
                size_bytes=len(item.processed.data),
                etag=item.stored.etag,
                width=item.processed.width,
                height=item.processed.height,
                image_type=ImageType.AFTER,
                uploaded_by_staff_id=staff_id,
            )

            session.add(image)
            images.append(image)

        await session.flush()

        # เอา created_at ที่ DB สร้างให้กลับมาใช้ใน response
        for image in images:
            await session.refresh(image)

        await session.commit()
        committed = True

    except SQLAlchemyError:
        raise
    finally:
        if not committed:
            try:
                await session.rollback()
            finally:
                for item in prepared:
                    try:
                        await storage.delete(item.stored.object_key)
                    except Exception:
                        # cleanup failure ไม่ควรกลบ error หลัก
                        pass

    return images