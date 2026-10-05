"""API endpoints สำหรับล็อกอินและอ่านข้อมูลผู้ใช้ปัจจุบัน."""

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.dependencies import CurrentStaff, DbSession
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_session_factory
from app.models.staff import Staff
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.password_reset import (
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordResetRequestAccepted,
    PasswordResetTokenRequest,
    PasswordResetValidationResponse,
)
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
from app.services.password_reset import (
    InvalidResetTokenError,
    confirm_password_reset,
    deliver_password_reset,
    request_password_reset,
    validate_reset_token,
)
from app.services.rate_limit import SlidingWindowRateLimiter

logger = logging.getLogger(__name__)
router = APIRouter()

SessionFactory = Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)]


def _password_reset_limiter(request: Request) -> SlidingWindowRateLimiter:
    """One limiter per application instance, created on first use."""
    limiter = getattr(request.app.state, "password_reset_limiter", None)
    if limiter is None:
        limiter = SlidingWindowRateLimiter(
            limit=settings.password_reset_ip_limit,
            window_seconds=settings.password_reset_ip_window_seconds,
        )
        request.app.state.password_reset_limiter = limiter
    return limiter


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


@router.post(
    "/password-reset-requests",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=PasswordResetRequestAccepted,
)
async def request_reset_link(
    payload: PasswordResetRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    session: DbSession,
    session_factory: SessionFactory,
) -> PasswordResetRequestAccepted:
    """Always answer 202 with the same body; email is sent after the response."""
    # request.client is the real client only when Uvicorn trusts the proxy's
    # X-Forwarded-For (FORWARDED_ALLOW_IPS); otherwise every user shares Nginx's IP.
    client_ip = request.client.host if request.client else "unknown"
    if not _password_reset_limiter(request).allow(client_ip):
        logger.warning("Password reset request rate-limited by IP")
        return PasswordResetRequestAccepted()

    pending = await request_password_reset(session, payload.email)
    if pending is not None:
        background_tasks.add_task(deliver_password_reset, session_factory, pending)
    return PasswordResetRequestAccepted()


@router.post("/password-reset/validate", response_model=PasswordResetValidationResponse)
async def validate_reset_link(
    payload: PasswordResetTokenRequest, session: DbSession
) -> PasswordResetValidationResponse:
    """Tell the reset page early whether the link can still be used."""
    try:
        await validate_reset_token(session, payload.token)
    except InvalidResetTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return PasswordResetValidationResponse()


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_reset(payload: PasswordResetConfirmRequest, session: DbSession) -> None:
    """Set the new password once; every earlier login session stops working."""
    try:
        await confirm_password_reset(
            session, token=payload.token, new_password=payload.new_password
        )
    except InvalidResetTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
