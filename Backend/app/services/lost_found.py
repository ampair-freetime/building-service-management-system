"""Business logic ร่วมของ guest lost/found endpoints."""

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import LostStatus, LostType
from app.models.image import Image
from app.models.location import Location
from app.models.lost_found import LostItem, LostItemHistory
from app.schemas.lost_found_item import (
    GuestFoundItemCreate,
    GuestImageResponse,
    GuestItemCreateBase,
    GuestItemCreatedResponse,
    GuestItemListResponse,
    GuestItemPublicResponse,
    Guest_Tracking_Request,
    Guest_Tracking_Response
)
from app.services.images import prepare_guest_image
from app.services.object_storage import (
    ObjectStorage,
    StorageOperationError,
    StoredObject,
)

logger = logging.getLogger(__name__)


class LocationNotFoundError(ValueError):
    """location_id ไม่มีอยู่หรือถูกปิดใช้งาน."""


class PublicItemNotFoundError(LookupError):
    """ไม่พบประกาศ public ที่ตรงกับประเภทและรหัส."""


class ItemPersistenceError(RuntimeError):
    """ไม่สามารถบันทึกรายงานลงฐานข้อมูลได้."""


async def create_guest_item(
    session: AsyncSession,
    *,
    payload: GuestItemCreateBase,
    report_type: LostType,
    image_upload: UploadFile | None,
    storage: ObjectStorage,
) -> GuestItemCreatedResponse:
    """ตรวจข้อมูล อัปโหลดรูป แล้ว commit ประกาศกับ image metadata พร้อมกัน."""
    if payload.location_id is not None:
        location = await session.get(Location, payload.location_id)
        if location is None or not location.is_active:
            raise LocationNotFoundError("ไม่พบสถานที่ที่เลือกหรือสถานที่ถูกปิดใช้งาน")

    item_id = uuid4()
    item_code = _make_item_code(report_type, item_id)
    processed = None
    stored: StoredObject | None = None
    image_id: UUID | None = None

    if image_upload is not None:
        processed = await prepare_guest_image(image_upload)
        image_id = uuid4()
        object_key = f"lost-found/{report_type.value}/{item_id}/{image_id}.webp"
        stored = await storage.put(
            object_key=object_key,
            data=processed.data,
            content_type=processed.content_type,
        )

    private_verification_detail = None
    custody_location = None
    if isinstance(payload, GuestFoundItemCreate):
        private_verification_detail = payload.private_verification_detail
        custody_location = payload.custody_location

    item = LostItem(
        id=item_id,
        item_code=item_code,
        report_type=report_type,
        item_category=payload.item_category,
        item_name=payload.item_name,
        description=payload.description,
        event_datetime=payload.event_datetime,
        location_id=payload.location_id,
        location_detail=payload.location_detail,
        custody_location=custody_location,
        private_verification_detail=private_verification_detail,
        reporter_email=str(payload.reporter_email),
        status=LostStatus.PENDING,
    )
    try:
        session.add(item)
        await session.flush()
        session.add(
            LostItemHistory(
                lost_item_id=item_id,
                old_status=None,
                new_status=LostStatus.APPROVED,
                note="Guest submitted report",
            )
        )
        if stored is not None and processed is not None and image_id is not None:
            session.add(
                Image(
                    id=image_id,
                    lost_item_id=item_id,
                    request_id=None,
                    object_key=stored.object_key,
                    storage_provider="r2",
                    bucket_name=stored.bucket_name,
                    content_type=processed.content_type,
                    size_bytes=len(processed.data),
                    etag=stored.etag,
                    width=processed.width,
                    height=processed.height,
                    image_type=None,
                    uploaded_by_staff_id=None,
                )
            )
        await session.commit()
        await session.refresh(item)
    except SQLAlchemyError as exc:
        await session.rollback()
        if stored is not None:
            try:
                await storage.delete(stored.object_key)
            except StorageOperationError:
                logger.exception(
                    "Failed to remove orphaned R2 object %s after DB rollback",
                    stored.object_key,
                )
        raise ItemPersistenceError("ไม่สามารถบันทึกประกาศได้") from exc

    return GuestItemCreatedResponse(
        id=item.id,
        item_code=item.item_code,
        report_type=item.report_type,
        status=item.status,
        message="รับรายงานแล้ว กรุณารอเจ้าหน้าที่ตรวจสอบก่อนเผยแพร่",
    )


async def list_public_items(
    session: AsyncSession,
    *,
    report_type: LostType,
    storage: ObjectStorage,
    limit: int,
    offset: int,
    category: str | None = None,
    search: str | None = None,
) -> GuestItemListResponse:
    """อ่านเฉพาะประกาศ approved และไม่ถูก soft-delete."""
    filters = [
        LostItem.report_type == report_type,
        LostItem.status == LostStatus.APPROVED,
        LostItem.deleted_at.is_(None),
    ]
    if category:
        filters.append(LostItem.item_category == category.strip())
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                LostItem.item_name.ilike(pattern),
                LostItem.description.ilike(pattern),
                LostItem.location_detail.ilike(pattern),
            )
        )

    total = await session.scalar(select(func.count(LostItem.id)).where(*filters))
    result = await session.scalars(
        select(LostItem)
        .where(*filters)
        .order_by(LostItem.created_at.desc(), LostItem.id.desc())
        .limit(limit)
        .offset(offset)
    )
    items = list(result)
    image_map = await _load_image_map(session, [item.id for item in items])

    return GuestItemListResponse(
        items=[_to_public_response(item, image_map.get(item.id, []), storage) for item in items],
        total=int(total or 0),
        limit=limit,
        offset=offset,
    )


async def get_public_item(
    session: AsyncSession,
    *,
    report_type: LostType,
    item_code: str,
    storage: ObjectStorage,
) -> GuestItemPublicResponse:
    """อ่านรายละเอียดประกาศ approved โดยไม่คืนข้อมูลส่วนตัวของผู้รายงาน."""
    item = await session.scalar(
        select(LostItem).where(
            LostItem.report_type == report_type,
            LostItem.item_code == item_code.strip().upper(),
            LostItem.status == LostStatus.APPROVED,
            LostItem.deleted_at.is_(None),
        )
    )
    if item is None:
        raise PublicItemNotFoundError("ไม่พบประกาศนี้")

    image_map = await _load_image_map(session, [item.id])
    return _to_public_response(item, image_map.get(item.id, []), storage)


async def _load_image_map(
    session: AsyncSession,
    item_ids: list[UUID],
) -> dict[UUID, list[Image]]:
    """โหลดรูปของหลายโพสต์ใน query เดียวเพื่อเลี่ยง N+1 queries."""
    if not item_ids:
        return {}

    result = await session.scalars(
        select(Image)
        .where(
            Image.lost_item_id.in_(item_ids),
            Image.deleted_at.is_(None),
        )
        .order_by(Image.created_at, Image.id)
    )
    image_map: dict[UUID, list[Image]] = {}
    for image in result:
        if image.lost_item_id is not None:
            image_map.setdefault(image.lost_item_id, []).append(image)
    return image_map


def _to_public_response(
    item: LostItem,
    images: list[Image],
    storage: ObjectStorage,
) -> GuestItemPublicResponse:
    return GuestItemPublicResponse(
        id=item.id,
        item_code=item.item_code,
        report_type=item.report_type,
        item_category=item.item_category,
        item_name=item.item_name,
        description=item.description,
        event_datetime=item.event_datetime,
        location_id=item.location_id,
        location_detail=item.location_detail,
        custody_location=item.custody_location,
        status=item.status,
        created_at=item.created_at,
        images=[
            GuestImageResponse(
                id=image.id,
                url=storage.create_download_url(image.object_key),
                content_type=image.content_type,
                width=image.width,
                height=image.height,
            )
            for image in images
        ],
    )
def track_guest_item(session: AsyncSession,item_id: str ,reporter_email: str) -> LostItem:

    return

def _make_item_code(report_type: LostType, item_id: UUID) -> str:
    """สร้าง tracking code ที่อ่านง่ายและแทบไม่มีโอกาสชนกัน."""
    prefix = "LOST" if report_type == LostType.LOST else "FOUND"
    date_part = datetime.now(UTC).strftime("%Y%m%d")
    return f"{prefix}-{date_part}-{item_id.hex[:8].upper()}"
