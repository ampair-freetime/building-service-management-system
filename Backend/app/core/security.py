"""เครื่องมือด้านความปลอดภัยสำหรับแฮชรหัสผ่านและจัดการ JWT."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings

# ใช้ค่าที่ pwdlib แนะนำ (ปัจจุบันคือ Argon2) เพื่อไม่ต้องกำหนดพารามิเตอร์เอง
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """แปลงรหัสผ่านจริงเป็นค่าแฮชก่อนบันทึกลงฐานข้อมูล."""
    return password_hash.hash(password)


def verify_password(password: str, encoded_hash: str) -> bool:
    """ตรวจว่ารหัสผ่านที่กรอกตรงกับค่าแฮชในฐานข้อมูลหรือไม่."""
    return password_hash.verify(password, encoded_hash)


def create_access_token(staff_id: UUID, role: str) -> str:
    """สร้าง JWT อายุจำกัด โดยระบุเจ้าของ token และบทบาทของพนักงาน."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(staff_id),  # subject: UUID ของเจ้าของ token
        "role": role,
        "type": "access",  # ป้องกัน token ชนิดอื่นถูกนำมาใช้แทน access token
        "iat": now,  # เวลาที่ออก token
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> UUID:
    """ตรวจลายเซ็น/วันหมดอายุของ JWT แล้วคืน UUID ของพนักงาน."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            # จำกัด algorithm ที่ยอมรับ ป้องกันผู้ส่ง token เลือก algorithm เอง
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            raise InvalidTokenError("Unexpected token type")
        return UUID(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        # ซ่อนรายละเอียดภายในไว้ และให้ชั้น API ตอบเป็น 401 แบบเดียวกัน
        raise ValueError("Invalid access token") from exc
