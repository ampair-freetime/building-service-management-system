"""Business logic สำหรับตรวจสอบข้อมูลล็อกอิน."""

import asyncio
from datetime import UTC, datetime
from functools import cache

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.core.security import hash_password, verify_password
from app.models.enums import AccountStatus
from app.models.staff import Staff
from app.services.staff import get_staff_by_email


async def authenticate_staff(
    session: AsyncSession, identifier: str, password: str
) -> Staff | None:
    """คืนบัญชีเมื่อข้อมูลถูกต้อง หรือคืน None เมื่อไม่ผ่านการยืนยันตัวตน."""
    account = await get_staff_by_email(session, identifier)
    usable = account is not None and account.status == AccountStatus.ACTIVE

    # ตรวจ argon2 ทุกครั้ง แม้ไม่มีบัญชีนี้ (เทียบกับ hash หลอก) เพื่อให้เวลาตอบเท่ากัน
    # ไม่อย่างนั้นคนนอกจับเวลาแล้วรู้ได้ว่าอีเมลไหนมีบัญชีอยู่
    encoded_hash = account.password_hash if usable else _dummy_hash()
    # argon2 ใช้ CPU ราว 50 ms ต่อครั้ง ถ้ารันใน event loop ตรง ๆ request อื่นทั้งหมดจะต้องรอ
    # จึงย้ายไปรันใน thread pool แทน
    password_ok = await asyncio.to_thread(verify_password, password, encoded_hash)

    # บัญชีที่ถูกปิดใช้งานต้องล็อกอินไม่ได้ แม้รหัสผ่านจะถูกต้อง
    if not usable or not password_ok:
        return None
    return account


@cache
def _dummy_hash() -> str:
    """hash ของรหัสที่ไม่มีใครรู้ สร้างครั้งเดียวแล้วจำไว้ ใช้แค่ถ่วงเวลาให้เท่ากับบัญชีจริง"""
    return hash_password("timing-equaliser-not-a-real-password")


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
