"""Business logic และคำสั่งฐานข้อมูลที่เกี่ยวกับบัญชีพนักงาน."""

import asyncio
import logging
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_temporary_password, hash_password
from app.models.enums import AccountStatus
from app.models.staff import Staff
from app.schemas.staff import StaffCreate
from app.services.email import EmailDeliveryError, build_staff_welcome_email, send_email

logger = logging.getLogger(__name__)


class DuplicateStaffError(Exception):
    """แจ้งว่ารหัสพนักงานหรืออีเมลซ้ำกับบัญชีที่มีอยู่."""


async def get_staff_by_id(session: AsyncSession, staff_id: UUID) -> Staff | None:
    """ค้นหาพนักงานด้วย UUID ซึ่งใช้เป็น subject ภายใน JWT."""
    return await session.get(Staff, staff_id)


async def get_staff_by_identifier(
    session: AsyncSession, identifier: str
) -> Staff | None:
    """ค้นหาบัญชีด้วยอีเมลหรือรหัสพนักงาน โดยไม่สนตัวพิมพ์ของข้อมูลที่รับมา."""
    normalized = identifier.strip()
    statement = select(Staff).where(
        or_(
            Staff.email == normalized.lower(),
            Staff.staff_code == normalized.upper(),
        )
    )
    return await session.scalar(statement)


async def list_staff(session: AsyncSession) -> list[Staff]:
    """คืนบัญชีพนักงานทั้งหมด เรียงตามรหัสพนักงาน."""
    result = await session.scalars(select(Staff).order_by(Staff.staff_code))
    return list(result)


async def create_staff(session: AsyncSession, payload: StaffCreate) -> tuple[Staff, str]:
    """สุ่มและแฮชรหัสผ่าน จากนั้นบันทึกบัญชีก่อนคืนรหัสจริงสำหรับส่งเมล."""
    temporary_password = generate_temporary_password()
    account = Staff(
        staff_code=payload.staff_code,
        email=str(payload.email),
        full_name=payload.full_name,
        # แฮชก่อนสร้าง model เพื่อไม่ให้รหัสผ่านจริงถูกบันทึก
        password_hash=hash_password(temporary_password),
        role=payload.role,
        status=AccountStatus.ACTIVE,
    )
    session.add(account)
    try:
        await session.commit()
    except IntegrityError as exc:
        # unique constraint เป็นด่านสุดท้ายที่กันคำขอพร้อมกันสร้างข้อมูลซ้ำ
        await session.rollback()
        raise DuplicateStaffError("Staff code or email already exists") from exc

    # โหลดค่าที่ฐานข้อมูลสร้างให้ เช่น created_at และ updated_at
    await session.refresh(account)
    return account, temporary_password


async def create_staff_and_send_credentials(
    session: AsyncSession, payload: StaffCreate
) -> tuple[Staff, bool]:
    """สร้างบัญชีให้สำเร็จก่อน แล้วส่งรหัสผ่านโดยไม่เปิดเผยใน API."""
    account, temporary_password = await create_staff(session, payload)
    subject, body = build_staff_welcome_email(
        full_name=account.full_name,
        staff_code=account.staff_code,
        email=account.email,
        temporary_password=temporary_password,
    )
    try:
        await asyncio.to_thread(send_email, to=account.email, subject=subject, text_body=body)
    except EmailDeliveryError:
        logger.warning("Unable to send staff welcome email for staff_id=%s", account.id)
        return account, False
    return account, True
