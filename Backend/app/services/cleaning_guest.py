"""Business logic ของ guest cleaning request endpoints."""

import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import ImageType, RequestAction, RequestStatus, RequestType
from app.models.image import Image
from app.models.location import Location
from app.models.service_request import RequestHistory, ServiceRequest
from app.schemas.cleaning_guest import (
    GuestCleaningCreate,
    GuestCleaningCreateResponse,
    GuestLocationResponse,
    GuestTrackingResponse,
)
from app.services.images import ProcessedImage, prepare_guest_image
from app.services.object_storage import (
    ObjectStorage,
    StorageConfigurationError,
    StorageOperationError,
    StoredObject,
)
from app.services.notification import create_cleaning_request_notifications

logger = logging.getLogger(__name__)
BANGKOK_TIMEZONE = ZoneInfo("Asia/Bangkok")


class LocationNotFoundError(ValueError):
    """QR token หรือ location_id ไม่มีอยู่หรือถูกปิดใช้งาน."""


class RequestNotFoundError(LookupError):
    """ไม่พบคำร้องที่ตรงกับรหัสและอีเมลผู้แจ้ง."""


class RequestPersistenceError(RuntimeError):
    """ไม่สามารถบันทึกคำร้องลงฐานข้อมูลได้."""


@dataclass(frozen=True)
class _PreparedImage:
    """รูปที่อัปขึ้น R2 แล้วแต่ยังไม่มีแถวในฐานข้อมูลอ้างถึง."""

    image_id: UUID
    processed: ProcessedImage
    stored: StoredObject


async def list_guest_locations(session: AsyncSession) -> list[GuestLocationResponse]:
    """คืนสถานที่ที่เปิดใช้งานสำหรับ dropdown ของ guest."""
    locations = await session.scalars(
        select(Location)
        .where(Location.is_active.is_(True))
        .order_by(Location.building, Location.floor, Location.room, Location.id)
    )
    return [
        GuestLocationResponse(
            id=location.id,
            building=location.building,
            floor=location.floor,
            room=location.room,
            area_type=location.area_type,
        )
        for location in locations
    ]


async def resolve_location_by_qr(
    session: AsyncSession,
    *,
    qr_token: str,
) -> GuestLocationResponse:
    """แปลง QR token เป็นสถานที่ให้ guest ยืนยันก่อนกรอกฟอร์ม.

    คืน id กลับไปด้วยเพื่อให้ frontend แนบเป็น hidden field ตอน POST
    ฟอร์มจึงผูกคำร้องกับแถวใน locations ได้ แทนที่จะเหลือแต่ข้อความที่ผู้ใช้พิมพ์เอง
    """
    location = await session.scalar(
        select(Location).where(
            Location.qr_token == qr_token.strip(),
            Location.is_active.is_(True),
        )
    )
    if location is None:
        raise LocationNotFoundError("ไม่พบสถานที่จาก QR code นี้ หรือสถานที่ถูกปิดใช้งาน")

    return GuestLocationResponse(
        id=location.id,
        building=location.building,
        floor=location.floor,
        room=location.room,
        area_type=location.area_type,
    )


async def create_guest_cleaning_request(
    session: AsyncSession,
    *,
    payload: GuestCleaningCreate,
    image_upload: UploadFile | None,
    storage: ObjectStorage | None,
) -> GuestCleaningCreateResponse:
    """เตรียมคำร้อง รูป และ response ให้ครบก่อน commit ฐานข้อมูล."""
    # Dropdown และ QR ผ่าน client จึงต้องตรวจสถานที่ซ้ำก่อนบันทึก
    location = await session.get(Location, payload.location_id)
    if location is None or not location.is_active:
        raise LocationNotFoundError("ไม่พบสถานที่ที่เลือกหรือสถานที่ถูกปิดใช้งาน")
    # สร้าง id เองก่อนแตะฐานข้อมูล เพราะต้องใช้ตั้งชื่อ object key ใน R2 ตั้งแต่ขั้นอัปโหลด
    request_id = uuid4()
    request_code = _make_request_code(request_id)
    prepared: list[_PreparedImage] = []
    service_request = ServiceRequest(
        id=request_id,
        request_code=request_code,
        request_type=RequestType.CLEANING,
        location_id=location.id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status=RequestStatus.WAITING,
        reporter_email=str(payload.reporter_email),
        assigned_staff_id=None,
    )
    committed = False
    try:
        if _has_uploaded_file(image_upload):
            if storage is None:
                raise StorageConfigurationError("Object storage is not configured")
            processed = await prepare_guest_image(image_upload)
            image_id = uuid4()
            stored = await storage.put(
                object_key=f"cleaning/{request_id}/{image_id}.webp",
                data=processed.data,
                content_type=processed.content_type,
            )
            prepared.append(_PreparedImage(image_id=image_id, processed=processed, stored=stored))

        session.add(service_request)
        await session.flush()
        session.add(
            RequestHistory(
                request_id=request_id,
                action=RequestAction.CREATED,
                performed_by=None,
                target_staff_id=None,
                old_status=None,
                new_status=RequestStatus.WAITING,
                note="Guest submitted cleaning request",
            )
        )
        await create_cleaning_request_notifications(
            session,
            request_id=request_id,
            request_code=request_code,
            request_title=payload.title,
        )
        for item in prepared:
            session.add(
                Image(
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
                    # CheckConstraint image_parent_check บังคับว่ารูปที่ผูกกับ request_id
                    # ต้องมี image_type เสมอ ต่างจากรูปของ lost item ที่ต้องเป็น NULL
                    image_type=ImageType.BEFORE,
                    uploaded_by_staff_id=None,
                )
            )
        # ส่งคำร้อง ประวัติ และข้อมูลรูปลง DB ภายใน transaction เดียวกันก่อนยืนยัน
        await session.flush()
        await session.refresh(service_request, attribute_names=["created_at"])
        response = GuestCleaningCreateResponse(
            request_code=service_request.request_code,
            status=service_request.status,
            request_type=service_request.request_type,
            location=_format_location(location),
            image_count=len(prepared),
            created_at=service_request.created_at,
            message="รับคำร้องแล้ว กรุณาเก็บรหัสคำร้องไว้ใช้ติดตามสถานะ",
        )
        # หลัง commit ไม่อ่าน ORM หรือสร้าง response อีก เพื่อไม่ให้สำเร็จแล้วตอบ error
        await session.commit()
        committed = True
    except SQLAlchemyError as exc:
        raise RequestPersistenceError("ไม่สามารถบันทึกคำร้องได้") from exc
    finally:
        # asyncio.CancelledError สืบทอดจาก BaseException จึงไม่ถูก except ด้านบนจับ
        # ต้องเก็บกวาดใน finally เท่านั้น ไม่งั้นไฟล์ค้างใน R2 โดยไม่มีแถวอ้างถึง
        if not committed:
            try:
                await session.rollback()
            finally:
                await _discard_stored_objects(storage, prepared)

    return response


async def get_guest_request_status(
    session: AsyncSession,
    *,
    request_code: str,
    reporter_email: str,
) -> GuestTrackingResponse:
    """ติดตามสถานะคำร้องโดยใช้รหัสคู่กับอีเมลผู้แจ้งเป็นการพิสูจน์ตัวตน."""
    service_request = await session.scalar(
        select(ServiceRequest)
        # โหลดสถานที่ล่วงหน้า เพื่อไม่ให้การอ่าน relationship เรียก async I/O โดยไม่ await
        .options(
            selectinload(ServiceRequest.location),
        )
        .where(
            ServiceRequest.request_type == RequestType.CLEANING,
            ServiceRequest.request_code == request_code.strip().upper(),
            # อีเมลถูก normalize เป็นตัวพิมพ์เล็กตั้งแต่ตอนสร้าง จึงต้องเทียบด้วยรูปแบบเดียวกัน
            ServiceRequest.reporter_email == reporter_email.strip().lower(),
        )
    )
    if service_request is None:
        # ใช้ข้อความเดียวกันทั้งกรณีไม่มีรหัสนี้และกรณีอีเมลไม่ตรง เพื่อกันการไล่เดาอีเมลผู้แจ้ง
        raise RequestNotFoundError("ไม่พบคำร้องนี้")

    return GuestTrackingResponse(
        request_type=service_request.request_type,
        location=_format_location(service_request.location),
        status=service_request.status,
        created_at=service_request.created_at,
        updated_at=service_request.updated_at,
        completed_at=service_request.completed_at,
    )


async def _discard_stored_objects(
    storage: ObjectStorage | None,
    prepared: list[_PreparedImage],
) -> None:
    """ลบไฟล์ที่อัปขึ้น R2 ไปแล้วเมื่อคำร้องบันทึกไม่สำเร็จ."""
    if storage is None:
        return
    for item in prepared:
        try:
            await storage.delete(item.stored.object_key)
        except StorageOperationError:
            logger.exception(
                "Failed to remove orphaned R2 object %s after DB rollback",
                item.stored.object_key,
            )


def _format_location(location: Location) -> str:
    """ประกอบชื่อสถานที่ที่ลงทะเบียนไว้สำหรับแสดงผล."""
    parts = [location.building]
    if location.floor:
        parts.append(f"ชั้น {location.floor}")
    if location.room:
        parts.append(f"ห้อง {location.room}")
    if location.area_type:
        parts.append(location.area_type)
    return " ".join(parts)


def _has_uploaded_file(upload: UploadFile | None) -> bool:
    """input type=file ที่ว่างเปล่ามาถึงเป็น UploadFile ที่ filename เป็นค่าว่าง ไม่ใช่ None."""
    return upload is not None and bool(upload.filename)


def _make_request_code(request_id: UUID) -> str:
    """สร้างรหัสคำร้องที่อ่านง่ายและแทบไม่มีโอกาสชนกัน."""
    # ผู้ใช้อ่านรหัสนี้เทียบกับวันที่ตัวเองแจ้ง จึงต้องเป็นเวลาไทย ไม่ใช่ UTC
    date_part = datetime.now(BANGKOK_TIMEZONE).strftime("%Y%m%d")
    return f"CLN-{date_part}-{request_id.hex[:8].upper()}"
