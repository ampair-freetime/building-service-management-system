"""API endpoints สำหรับให้แอดมินสร้างและดูบัญชีพนักงาน."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AdminStaff, DbSession
from app.schemas.staff import StaffCreate, StaffCreatedResponse, StaffResponse
from app.services.invitations import (
    InvitationNotAvailableError,
    create_staff_and_invite,
    resend_staff_invitation,
)
from app.services.staff import DuplicateStaffError, list_staff

router = APIRouter()


@router.get("", response_model=list[StaffResponse])
async def read_staff(session: DbSession, _admin: AdminStaff) -> list[StaffResponse]:
    """แสดงบัญชีพนักงานทั้งหมด โดย FastAPI ตรวจสิทธิ์ admin ก่อนเรียกฟังก์ชัน."""
    accounts = await list_staff(session)
    return [StaffResponse.model_validate(account) for account in accounts]


@router.post("", response_model=StaffCreatedResponse, status_code=status.HTTP_201_CREATED)
async def add_staff(
    payload: StaffCreate, session: DbSession, _admin: AdminStaff
) -> StaffCreatedResponse:
    """สร้างบัญชีพนักงานใหม่ โดยอนุญาตเฉพาะ admin."""
    try:
        result = await create_staff_and_invite(session, payload)
    except DuplicateStaffError as exc:
        # HTTP 409 หมายถึงข้อมูลใหม่ขัดแย้งกับบัญชีที่มีอยู่แล้ว
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return StaffCreatedResponse(
        **StaffResponse.model_validate(result.staff).model_dump(), email_sent=result.invitation_sent
    )


@router.post("/{staff_id}/resend-invitation", response_model=StaffCreatedResponse)
async def resend_invitation(
    staff_id: UUID, session: DbSession, _admin: AdminStaff
) -> StaffCreatedResponse:
    """Issue a fresh link for an existing unactivated account without duplicating it."""
    try:
        result = await resend_staff_invitation(session, staff_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvitationNotAvailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return StaffCreatedResponse(
        **StaffResponse.model_validate(result.staff).model_dump(), email_sent=result.invitation_sent
    )
