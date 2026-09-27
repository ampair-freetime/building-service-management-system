"""API endpoints สำหรับล็อกอินและอ่านข้อมูลผู้ใช้ปัจจุบัน."""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentStaff, DbSession
from app.core.security import create_access_token
from app.models.staff import Staff
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.staff import (
    ActivationRequest,
    ActivationTokenRequest,
    ActivationValidationResponse,
    StaffResponse,
)
from app.services.invitations import (
    InvalidActivationTokenError,
    activate_staff_account,
    validate_activation_token,
)
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
async def read_current_staff(current_staff: CurrentStaff) -> Staff:
    """คืนโปรไฟล์ของเจ้าของ Bearer token ที่ผ่านการตรวจสอบแล้ว."""
    return current_staff


@router.post("/activation/validate", response_model=ActivationValidationResponse)
async def validate_activation(
    payload: ActivationTokenRequest, session: DbSession
) -> ActivationValidationResponse:
    """Reject invalid links without logging their token in a URL."""
    try:
        await validate_activation_token(session, payload.token)
    except InvalidActivationTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ActivationValidationResponse()


@router.post("/activation", status_code=status.HTTP_204_NO_CONTENT)
@router.post("/setup-password", status_code=status.HTTP_204_NO_CONTENT)
async def activate_account(payload: ActivationRequest, session: DbSession) -> None:
    """Set a first password exactly once after validating the invitation token."""
    try:
        await activate_staff_account(session, token=payload.token, password=payload.password)
    except InvalidActivationTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
