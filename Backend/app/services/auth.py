"""Business logic สำหรับตรวจสอบข้อมูลล็อกอิน."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.staff_account import StaffAccount
from app.services.staff import get_staff_by_identifier


async def authenticate_staff(
    session: AsyncSession, identifier: str, password: str
) -> StaffAccount | None:
    """คืนบัญชีเมื่อข้อมูลถูกต้อง หรือคืน None เมื่อไม่ผ่านการยืนยันตัวตน."""
    account = await get_staff_by_identifier(session, identifier)

    # บัญชีที่ถูกปิดใช้งานต้องล็อกอินไม่ได้ แม้รหัสผ่านจะถูกต้อง
    if account is None or not account.is_active:
        return None
    if not verify_password(password, account.password_hash):
        return None
    return account
