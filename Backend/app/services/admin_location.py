"""กฎธุรกิจสำหรับจัดการ location และ QR ของ Admin."""

import secrets
from urllib.parse import quote

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.location import Location
from app.models.lost_found import LostItem
from app.models.service_request import ServiceRequest
from app.schemas.admin_location import (
    AdminLocationCreate,
    AdminLocationResponse,
    AdminLocationUpdate,
)


class LocationNotFoundError(LookupError):
    """ไม่พบ location ที่ระบุ."""


class DuplicateLocationError(ValueError):
    """มี location ที่มี floor และ area เดียวกันแล้ว."""


class LocationInactiveError(ValueError):
    """ไม่อนุญาตให้จัดการ QR ของ location ที่ปิดอยู่."""


class QrNotGeneratedError(ValueError):
    """ยังไม่ได้สร้าง QR ให้ location นี้."""


class QrTokenCollisionError(ValueError):
    """QR token ที่สุ่มได้ชนกับ token ที่มีอยู่แล้ว."""


class LocationInUseError(ValueError):
    """location มีคำร้องหรือรายการของหายผูกอยู่ จึงลบไม่ได้ ต้องใช้ปิดใช้งานแทน."""


def build_qr_url(qr_token: str, base_url: str | None = None) -> str:
    """ประกอบ URL หน้า guest โดยเข้ารหัส token สำหรับ query string."""
    if base_url is None:
        base_url = settings.public_base_url
    return f"{base_url.rstrip('/')}/user?token={quote(qr_token, safe='')}"


def build_location_label(location: Location) -> str:
    return f"ชั้น {location.floor} {location.area}" if location.floor else location.area


def to_admin_response(location: Location) -> AdminLocationResponse:
    return AdminLocationResponse(
        id=location.id,
        floor=location.floor,
        area=location.area,
        label=build_location_label(location),
        is_active=location.is_active,
        qr_token=location.qr_token,
        qr_url=build_qr_url(location.qr_token) if location.qr_token else None,
        created_at=location.created_at,
        updated_at=location.updated_at,
    )


async def get_location_or_raise(session: AsyncSession, location_id: int) -> Location:
    location = await session.get(Location, location_id)
    if location is None:
        raise LocationNotFoundError("Location not found")
    return location


async def get_location_for_qr(session: AsyncSession, *, location_id: int) -> Location:
    location = await get_location_or_raise(session, location_id)
    if not location.is_active:
        raise LocationInactiveError("Location is inactive")
    if location.qr_token is None:
        raise QrNotGeneratedError("QR has not been generated for this location")
    return location


async def list_locations(
    session: AsyncSession, *, include_inactive: bool = False
) -> list[AdminLocationResponse]:
    statement = select(Location)
    if not include_inactive:
        statement = statement.where(Location.is_active.is_(True))
    locations = await session.scalars(
        statement.order_by(Location.floor, Location.area, Location.id)
    )
    return [to_admin_response(location) for location in locations]


async def _duplicate_exists(
    session: AsyncSession, *, floor: str | None, area: str, ignore_id: int | None = None
) -> bool:
    # เปรียบเทียบแบบไม่แยกตัวพิมพ์ เพื่อให้ "Lobby" กับ "LOBBY"
    # เป็นสถานที่เดียวกัน โดยยังเก็บรูปแบบข้อความที่ผู้ใช้กรอกไว้สำหรับแสดงผล
    statement = select(Location.id).where(
        func.lower(func.coalesce(Location.floor, "")) == (floor or "").lower(),
        func.lower(Location.area) == area.lower(),
    )
    if ignore_id is not None:
        statement = statement.where(Location.id != ignore_id)
    return await session.scalar(statement.limit(1)) is not None


async def _commit_or_raise_duplicate(session: AsyncSession) -> None:
    """unique index เป็นด่านสุดท้ายกันคำขอพร้อมกันที่ผ่าน _duplicate_exists มาทั้งคู่."""
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateLocationError("Location already exists") from exc


async def create_location(
    session: AsyncSession, payload: AdminLocationCreate
) -> AdminLocationResponse:
    if await _duplicate_exists(session, floor=payload.floor, area=payload.area):
        raise DuplicateLocationError("Location already exists")
    location = Location(floor=payload.floor, area=payload.area, qr_token=None)
    session.add(location)
    await _commit_or_raise_duplicate(session)
    await session.refresh(location)
    return to_admin_response(location)


async def update_location(
    session: AsyncSession, *, location_id: int, payload: AdminLocationUpdate
) -> AdminLocationResponse:
    location = await get_location_or_raise(session, location_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return to_admin_response(location)
    floor = changes.get("floor", location.floor)
    area = changes.get("area", location.area)
    if (floor, area) != (location.floor, location.area) and await _duplicate_exists(
        session, floor=floor, area=area, ignore_id=location_id
    ):
        raise DuplicateLocationError("Location already exists")
    for field, value in changes.items():
        setattr(location, field, value)
    await _commit_or_raise_duplicate(session)
    await session.refresh(location)
    return to_admin_response(location)


async def set_location_active(
    session: AsyncSession, *, location_id: int, is_active: bool
) -> AdminLocationResponse:
    location = await get_location_or_raise(session, location_id)
    if location.is_active == is_active:
        return to_admin_response(location)
    location.is_active = is_active
    await session.commit()
    await session.refresh(location)
    return to_admin_response(location)


async def generate_qr(session: AsyncSession, *, location_id: int) -> AdminLocationResponse:
    location = await get_location_or_raise(session, location_id)
    if not location.is_active:
        raise LocationInactiveError("Location is inactive")
    if location.qr_token is not None:
        return to_admin_response(location)
    new_token = secrets.token_urlsafe(24)
    try:
        result = await session.execute(
            update(Location)
            .where(
                Location.id == location_id,
                Location.is_active.is_(True),
                Location.qr_token.is_(None),
            )
            .values(qr_token=new_token)
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise QrTokenCollisionError("QR token collision; please retry") from exc
    await session.refresh(location)
    if result.rowcount == 0:
        if not location.is_active:
            raise LocationInactiveError("Location is inactive")
        if location.qr_token is None:
            raise LocationNotFoundError("Location not found")
    return to_admin_response(location)


async def regenerate_qr(session: AsyncSession, *, location_id: int) -> AdminLocationResponse:
    location = await get_location_for_qr(session, location_id=location_id)
    old_token = location.qr_token
    for _ in range(3):
        new_token = secrets.token_urlsafe(24)
        if new_token != old_token:
            break
    else:
        raise QrTokenCollisionError("Unable to generate a new QR token; please retry")
    location.qr_token = new_token
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise QrTokenCollisionError("QR token collision; please retry") from exc
    await session.refresh(location)
    return to_admin_response(location)


async def delete_location(session: AsyncSession, *, location_id: int) -> None:
    """ลบ location ที่สร้างผิดและยังไม่เคยถูกใช้ เพื่อให้ชื่อเดิมว่างให้สร้างใหม่ได้."""
    # ล็อกแถวก่อนนับ: guest ที่กำลังส่งคำร้องเข้าห้องนี้ต้องรอจนเราตัดสินเสร็จ
    location = await session.scalar(
        select(Location).where(Location.id == location_id).with_for_update()
    )
    if location is None:
        raise LocationNotFoundError("Location not found")

    # นับ lost_items ทุกแถวรวมที่ soft delete แล้ว เพราะยังมี foreign key ชี้ห้องนี้อยู่
    request_count = await session.scalar(
        select(func.count()).select_from(ServiceRequest).where(
            ServiceRequest.location_id == location_id
        )
    )
    lost_item_count = await session.scalar(
        select(func.count()).select_from(LostItem).where(LostItem.location_id == location_id)
    )
    if request_count or lost_item_count:
        await session.rollback()
        raise LocationInUseError(
            f"สถานที่นี้มีคำร้อง {request_count} รายการและรายการของหาย/ของที่พบ "
            f"{lost_item_count} รายการ จึงลบไม่ได้ ให้ใช้ปิดใช้งานแทน"
        )

    await session.delete(location)
    try:
        await session.commit()
    except IntegrityError as exc:
        # ตาข่ายกันตก: foreign key ของ DB ปฏิเสธเมื่อมีข้อมูลผูกที่การนับไม่เห็น
        await session.rollback()
        raise LocationInUseError("สถานที่นี้มีข้อมูลผูกอยู่ จึงลบไม่ได้ ให้ใช้ปิดใช้งานแทน") from exc
