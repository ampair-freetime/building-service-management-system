"""Business logic ของ guest repair request endpoints."""

import logging
from datetime import datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.models.enums import ImageType, RequestAction, RequestStatus, RequestType
from app.models.location import Location
from app.models.service_request import RequestHistory, ServiceRequest
from app.schemas.repair_guest import (
    GuestRepairCreate,
    GuestRepairCreateResponse,
    GuestRepairLocationResponse,
    GuestRepairTrackingResponse,
)
from app.services.notification import create_repair_request_notifications
from app.services.object_storage import (
    ObjectStorage,
)
from app.services.photo_attachments import stage_photos

logger = logging.getLogger(__name__)
REPAIR_CODE_PREFIX = "RPR"
REPAIR_STORAGE_PREFIX = "repair"
REPAIR_HISTORY_NOTE = "Guest submitted repair request"
BANGKOK_TIMEZONE = ZoneInfo("Asia/Bangkok")


class RepairLocationNotFoundError(ValueError):
    """QR token หรือ location_id ไม่มีอยู่หรือถูกปิดใช้งาน."""


class RepairRequestNotFoundError(LookupError):
    """ไม่พบคำร้องที่ตรงกับรหัสและอีเมลผู้แจ้ง."""


class RepairRequestPersistenceError(RuntimeError):
    """ไม่สามารถบันทึกคำร้องลงฐานข้อมูลได้."""


async def list_guest_repair_locations(session: AsyncSession) -> list[GuestRepairLocationResponse]:
    """คืนสถานที่ที่เปิดใช้งานสำหรับ dropdown ของ guest."""
    locations = await session.scalars(
        select(Location)
        .where(Location.is_active.is_(True))
        .order_by(Location.floor, Location.area, Location.id)
    )
    return [
        GuestRepairLocationResponse(
            id=location.id,
            floor=location.floor,
            area=location.area,
        )
        for location in locations
    ]


async def resolve_guest_repair_location_by_qr(
    session: AsyncSession,
    *,
    qr_token: str,
) -> GuestRepairLocationResponse:
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
        raise RepairLocationNotFoundError("ไม่พบสถานที่จาก QR code นี้ หรือสถานที่ถูกปิดใช้งาน")

    return GuestRepairLocationResponse(
        id=location.id,
        floor=location.floor,
        area=location.area,
    )


async def create_guest_repair_request(
    session: AsyncSession,
    *,
    payload: GuestRepairCreate,
    image_uploads: list[UploadFile],
    storage: ObjectStorage | None,
) -> GuestRepairCreateResponse:
    """อัปโหลดรูปก่อน แล้วเตรียมคำร้องและ response ให้ครบก่อน commit ฐานข้อมูล."""
    # สร้าง id เองก่อนแตะฐานข้อมูล เพราะต้องใช้ตั้งชื่อ object key ใน R2 ตั้งแต่ขั้นอัปโหลด
    request_id = uuid4()
    request_code = _make_request_code(request_id)
    # อัปรูปขึ้น R2 ก่อนเปิด transaction จะได้ไม่ถือ connection ไว้ระหว่างรออัปโหลด
    async with await stage_photos(
        storage, image_uploads, key_prefix=f"{REPAIR_STORAGE_PREFIX}/{request_id}"
    ) as photos:
        # Dropdown และ QR ผ่าน client จึงต้องตรวจสถานที่ซ้ำก่อนบันทึก
        location = await session.get(Location, payload.location_id)
        if location is None or not location.is_active:
            raise RepairLocationNotFoundError("ไม่พบสถานที่ที่เลือกหรือสถานที่ถูกปิดใช้งาน")
        service_request = ServiceRequest(
            id=request_id,
            request_code=request_code,
            request_type=RequestType.REPAIR,
            location_id=location.id,
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            status=RequestStatus.WAITING,
            reporter_email=str(payload.reporter_email),
            assigned_staff_id=None,
        )
        commit_started = False
        try:
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
                    note=REPAIR_HISTORY_NOTE,
                )
            )
            await create_repair_request_notifications(
                session,
                request_id=request_id,
                request_code=request_code,
                request_title=payload.title,
            )
            session.add_all(
                photos.image_rows(request_id=request_id, image_type=ImageType.BEFORE)
            )
            # ส่งคำร้อง ประวัติ และข้อมูลรูปลง DB ภายใน transaction เดียวกันก่อนยืนยัน
            await session.flush()
            await session.refresh(service_request, attribute_names=["created_at"])
            response = GuestRepairCreateResponse(
                request_code=service_request.request_code,
                status=service_request.status,
                request_type=service_request.request_type,
                location=_format_location(location),
                image_count=len(photos),
                created_at=service_request.created_at,
                message="รับคำร้องแจ้งซ่อมแล้ว ระบบจะส่งรหัสคำร้องไปทางอีเมล กรุณาเก็บรหัสไว้ใช้ติดตามสถานะ",
            )
            # หลัง commit ไม่อ่าน ORM หรือสร้าง response อีก เพื่อไม่ให้สำเร็จแล้วตอบ error
            commit_started = True
            await session.commit()
        except BaseException as exc:
            await session.rollback()
            if not commit_started:
                if isinstance(exc, SQLAlchemyError):
                    raise RepairRequestPersistenceError("ไม่สามารถบันทึกคำร้องได้") from exc
                raise
            # commit พังกลางทาง: ฐานข้อมูลอาจบันทึกไปแล้วก็ได้ จึงถามด้วย session ใหม่
            # ถ้าถามไม่ได้หรือถูกยกเลิกระหว่างนั้น ให้เก็บรูปไว้ ดีกว่าลบรูปของคำร้องที่บันทึกแล้ว
            saved = None
            try:
                if isinstance(exc, SQLAlchemyError):
                    saved = await _request_was_committed(session, request_id)
            except SQLAlchemyError:
                logger.exception("Cannot verify repair commit: request_id=%s", request_id)
            finally:
                if saved is None:
                    logger.warning(
                        "Repair commit unresolved; retaining images: request_id=%s keys=%s",
                        request_id,
                        photos.object_keys,
                    )
                    photos.keep()
            if not isinstance(exc, SQLAlchemyError):
                raise
            if not saved:
                raise RepairRequestPersistenceError("ไม่สามารถบันทึกคำร้องได้") from exc
        photos.keep()

    return response


async def get_guest_repair_status(
    session: AsyncSession,
    *,
    request_code: str,
    reporter_email: str,
) -> GuestRepairTrackingResponse:
    """ติดตามสถานะคำร้องโดยใช้รหัสคู่กับอีเมลผู้แจ้งเป็นการพิสูจน์ตัวตน."""
    service_request = await session.scalar(
        select(ServiceRequest)
        # โหลดสถานที่ล่วงหน้า เพื่อไม่ให้การอ่าน relationship เรียก async I/O โดยไม่ await
        .options(
            selectinload(ServiceRequest.location),
        )
        .where(
            ServiceRequest.request_type == RequestType.REPAIR,
            ServiceRequest.request_code == request_code.strip().upper(),
            # อีเมลถูก normalize เป็นตัวพิมพ์เล็กตั้งแต่ตอนสร้าง จึงต้องเทียบด้วยรูปแบบเดียวกัน
            ServiceRequest.reporter_email == reporter_email.strip().lower(),
        )
    )
    if service_request is None:
        # ใช้ข้อความเดียวกันทั้งกรณีไม่มีรหัสนี้และกรณีอีเมลไม่ตรง เพื่อกันการไล่เดาอีเมลผู้แจ้ง
        raise RepairRequestNotFoundError("ไม่พบคำร้องนี้")

    return GuestRepairTrackingResponse(
        request_type=service_request.request_type,
        title=service_request.title,
        location=_format_location(service_request.location),
        status=service_request.status,
        created_at=service_request.created_at,
        updated_at=service_request.updated_at,
        completed_at=service_request.completed_at,
    )


def _format_location(location: Location) -> str:
    """ประกอบชื่อสถานที่ที่ลงทะเบียนไว้สำหรับแสดงผล."""
    if location.floor:
        return f"ชั้น {location.floor} {location.area}"
    return location.area


def _make_request_code(request_id: UUID) -> str:
    """สร้างรหัสคำร้องที่อ่านง่ายและแทบไม่มีโอกาสชนกัน."""
    # ผู้ใช้อ่านรหัสนี้เทียบกับวันที่ตัวเองแจ้ง จึงต้องเป็นเวลาไทย ไม่ใช่ UTC
    date_part = datetime.now(BANGKOK_TIMEZONE).strftime("%Y%m%d")
    return f"{REPAIR_CODE_PREFIX}-{date_part}-{request_id.hex[:8].upper()}"


async def _request_was_committed(session: AsyncSession, request_id: UUID) -> bool:
    """ตรวจผลด้วย session ใหม่จาก engine เดิม ไม่ใช้ transaction ที่ล้มเหลว."""
    bind = session.bind
    if bind is None:
        raise SQLAlchemyError("Cannot verify commit without a database bind")
    # หาก caller bind กับ connection ให้เปิด connection ใหม่จาก engine แทน
    engine = bind.engine if isinstance(bind, AsyncConnection) else bind
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as verification_session:
        return (
            await verification_session.scalar(
                select(ServiceRequest.id).where(ServiceRequest.id == request_id)
            )
            is not None
        )
