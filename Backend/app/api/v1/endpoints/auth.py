"""API endpoints สำหรับล็อกอินและอ่านข้อมูลผู้ใช้ปัจจุบัน."""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentStaff, DbSession
from app.core.security import create_access_token
from app.models.staff_account import StaffAccount
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.staff import StaffResponse
from app.services.auth import authenticate_staff

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, session: DbSession) -> LoginResponse:
    """ตรวจข้อมูลล็อกอินและคืน JWT พร้อมข้อมูลพนักงานเมื่อสำเร็จ."""
    account = await authenticate_staff(session, payload.identifier, payload.password)
    if account is None:
        # ใช้ข้อความเดียวกันทั้งกรณีไม่พบบัญชีและรหัสผ่านผิด เพื่อลดการเดาบัญชี
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect identifier or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(account.id, account.role.value)
    return LoginResponse(access_token=token, staff=StaffResponse.model_validate(account))


@router.get("/me", response_model=StaffResponse)
async def read_current_staff(current_staff: CurrentStaff) -> StaffAccount:
    """คืนโปรไฟล์ของเจ้าของ Bearer token ที่ผ่านการตรวจสอบแล้ว."""
    return current_staff
