"""Business logic สำหรับตรวจสอบข้อมูลล็อกอิน."""

from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.core.security import verify_password
from app.models.enums import AccountStatus
from app.models.staff import Staff
from app.services.staff import get_staff_by_email


async def authenticate_staff(
    session: AsyncSession, identifier: str, password: str
) -> Staff | None:
    """คืนบัญชีเมื่อข้อมูลถูกต้อง หรือคืน None เมื่อไม่ผ่านการยืนยันตัวตน."""
    account = await get_staff_by_email(session, identifier)

    # บัญชีที่ถูกปิดใช้งานต้องล็อกอินไม่ได้ แม้รหัสผ่านจะถูกต้อง
    if account is None or account.status != AccountStatus.ACTIVE:
        return None
    if not verify_password(password, account.password_hash):
        return None
    return account


async def record_successful_login(session: AsyncSession, account: Staff) -> None:
    """บันทึกเวลาล็อกอินสำเร็จล่าสุด ให้ admin เห็นว่าบัญชีไหนยังถูกใช้งานอยู่

    ใช้ UPDATE ตรง ๆ และส่ง updated_at เดิมกลับไป เพื่อไม่ให้ onupdate ของ updated_at
    เปลี่ยนเวลา "แก้ไขข้อมูลล่าสุด" ทุกครั้งที่มีคน login
    """
    logged_in_at = datetime.now(UTC)
    await session.execute(
        update(Staff)
        .where(Staff.id == account.id)
        .values(last_login_at=logged_in_at, updated_at=Staff.updated_at)
    )
    await session.commit()
    # อัปเดตค่าใน object ที่ถืออยู่โดยไม่ทำให้ session มองว่ามีการแก้ค้างอยู่
    set_committed_value(account, "last_login_at", logged_in_at)
