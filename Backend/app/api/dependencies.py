"""Dependencies ที่ FastAPI ใช้เปิด session, ตรวจ JWT และตรวจสิทธิ์ผู้ใช้."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.models.enums import AccountStatus, StaffRole
from app.models.staff import Staff
from app.services.object_storage import (
    ObjectStorage,
    StorageConfigurationError,
    get_object_storage,
)
from app.services.staff import get_staff_by_id

# ปิด auto_error เพื่อให้ทุกกรณี token ผิดตอบด้วยข้อความ 401 รูปแบบเดียวกัน
bearer_scheme = HTTPBearer(auto_error=False)

# Type alias นี้ทำให้ endpoint ขอ database session ผ่าน Depends ได้แบบสั้นและอ่านง่าย
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_staff(
    session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> Staff:
    """ตรวจ Bearer token แล้วโหลดบัญชีพนักงานปัจจุบันจากฐานข้อมูล."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized

    try:
        staff_id = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise unauthorized from exc

    # อ่านข้อมูลล่าสุดจากฐานข้อมูลทุกครั้ง ไม่เชื่อ role/status ใน token เพียงอย่างเดียว
    account = await get_staff_by_id(session, staff_id)
    if account is None or account.status != AccountStatus.ACTIVE:
        raise unauthorized
    return account


# Endpoint ที่ประกาศพารามิเตอร์ชนิดนี้จะได้รับบัญชีของผู้ใช้ที่ล็อกอินแล้ว
CurrentStaff = Annotated[Staff, Depends(get_current_staff)]


async def require_admin(current_staff: CurrentStaff) -> Staff:
    """อนุญาตให้ทำงานต่อเฉพาะเมื่อผู้ใช้ปัจจุบันมีบทบาท admin."""
    if current_staff.role != StaffRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return current_staff


# ใช้กับ endpoint จัดการพนักงานเพื่อบังคับตรวจทั้ง token และบทบาท admin
AdminStaff = Annotated[Staff, Depends(require_admin)]


def provide_object_storage() -> ObjectStorage:
    """คืน R2 client หรือแจ้ง 503 แบบชัดเจนเมื่อ environment ยังไม่พร้อม."""
    try:
        return get_object_storage()
    except StorageConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ระบบจัดเก็บรูปภาพยังไม่ได้ตั้งค่า",
        ) from exc


ObjectStorageClient = Annotated[ObjectStorage, Depends(provide_object_storage)]
