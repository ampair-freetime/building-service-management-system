"""เครื่องมือด้านความปลอดภัยสำหรับแฮชรหัสผ่านและจัดการ JWT."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings

# ใช้ค่าที่ pwdlib แนะนำ (ปัจจุบันคือ Argon2) เพื่อไม่ต้องกำหนดพารามิเตอร์เอง
password_hash = PasswordHash.recommended()


PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
# ต้องตรงกับรายการเงื่อนไขที่หน้าเว็บแสดง (useStaffPasswordSetup / useStaffResetPassword)
_PASSWORD_RULES = (
    (re.compile(r"[A-Z]"), "Password must contain an uppercase letter"),
    (re.compile(r"[a-z]"), "Password must contain a lowercase letter"),
    (re.compile(r"\d"), "Password must contain a digit"),
    (re.compile(r"[^A-Za-z0-9]"), "Password must contain a special character"),
)


def validate_password_strength(password: str) -> str:
    """กฎรหัสผ่านกลางที่ใช้ทั้งตอน activate และตอนรีเซ็ต; ไม่ผ่านจะ raise ValueError."""
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise ValueError(
            f"Password must be {PASSWORD_MIN_LENGTH}-{PASSWORD_MAX_LENGTH} characters long"
        )
    for pattern, message in _PASSWORD_RULES:
        if not pattern.search(password):
            raise ValueError(message)
    return password


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
        # เก็บเศษวินาทีไว้ด้วย เพื่อเทียบกับ password_changed_at ได้แม่นยำ
        # (token ที่ออกก่อนเปลี่ยนรหัสในวินาทีเดียวกันต้องถูกตัดสิทธิ์)
        "iat": now.timestamp(),
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


@dataclass(frozen=True)
class AccessTokenClaims:
    staff_id: UUID
    issued_at: datetime


def decode_access_token(token: str) -> AccessTokenClaims:
    """ตรวจลายเซ็น/วันหมดอายุของ JWT แล้วคืน UUID ของพนักงานและเวลาที่ออก token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            # จำกัด algorithm ที่ยอมรับ ป้องกันผู้ส่ง token เลือก algorithm เอง
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "iat", "exp"]},
        )
        if payload.get("type") != "access":
            raise InvalidTokenError("Unexpected token type")
        return AccessTokenClaims(
            staff_id=UUID(payload["sub"]),
            issued_at=datetime.fromtimestamp(float(payload["iat"]), UTC),
        )
    except (InvalidTokenError, KeyError, TypeError, ValueError, OverflowError, OSError) as exc:
        # ซ่อนรายละเอียดภายในไว้ และให้ชั้น API ตอบเป็น 401 แบบเดียวกัน
        raise ValueError("Invalid access token") from exc
