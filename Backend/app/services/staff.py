"""Business logic และคำสั่งฐานข้อมูลที่เกี่ยวกับบัญชีพนักงาน."""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.staff_account import StaffAccount
from app.schemas.staff import StaffCreate


class DuplicateStaffError(Exception):
    """แจ้งว่ารหัสพนักงานหรืออีเมลซ้ำกับบัญชีที่มีอยู่."""


async def get_staff_by_id(session: AsyncSession, staff_id: UUID) -> StaffAccount | None:
    """ค้นหาพนักงานด้วย UUID ซึ่งใช้เป็น subject ภายใน JWT."""
    return await session.get(StaffAccount, staff_id)


async def get_staff_by_identifier(
    session: AsyncSession, identifier: str
) -> StaffAccount | None:
    """ค้นหาบัญชีด้วยอีเมลหรือรหัสพนักงาน โดยไม่สนตัวพิมพ์ของข้อมูลที่รับมา."""
    normalized = identifier.strip()
    statement = select(StaffAccount).where(
        or_(
            StaffAccount.email == normalized.lower(),
            StaffAccount.employee_code == normalized.upper(),
        )
    )
    return await session.scalar(statement)


async def list_staff(session: AsyncSession) -> list[StaffAccount]:
    """คืนบัญชีพนักงานทั้งหมด เรียงตามรหัสพนักงาน."""
    result = await session.scalars(select(StaffAccount).order_by(StaffAccount.employee_code))
    return list(result)


async def create_staff(session: AsyncSession, payload: StaffCreate) -> StaffAccount:
    """แฮชรหัสผ่าน สร้างบัญชี และบันทึกลงฐานข้อมูล."""
    account = StaffAccount(
        employee_code=payload.employee_code,
        email=str(payload.email),
        full_name=payload.full_name,
        # แฮชก่อนสร้าง model เพื่อไม่ให้รหัสผ่านจริงถูกบันทึก
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    session.add(account)
    try:
        await session.commit()
    except IntegrityError as exc:
        # unique constraint เป็นด่านสุดท้ายที่กันคำขอพร้อมกันสร้างข้อมูลซ้ำ
        await session.rollback()
        raise DuplicateStaffError("Employee code or email already exists") from exc

    # โหลดค่าที่ฐานข้อมูลสร้างให้ เช่น created_at และ updated_at
    await session.refresh(account)
    return account
