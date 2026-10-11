"""API endpoints สำหรับให้แอดมินสร้างและดูบัญชีพนักงาน."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AdminStaff, DbSession
from app.schemas.staff import (
    StaffCreate,
    StaffCreatedResponse,
    StaffResponse,
    StaffStatusUpdate,
    StaffUpdate,
)
from app.services.invitations import (
    InvitationNotAvailableError,
    create_staff_and_invite,
    resend_staff_invitation,
)
from app.services.staff import (
    DuplicateStaffError,
    StaffActorNotAuthorizedError,
    StaffChangeBlockedError,
    delete_staff_account,
    list_staff,
    set_staff_status,
    update_staff_profile,
)

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


@router.patch("/{staff_id}", response_model=StaffResponse)
async def edit_staff(
    staff_id: UUID, payload: StaffUpdate, session: DbSession, admin: AdminStaff
) -> StaffResponse:
    """Admin แก้ชื่อ/email โดยคง role, password และประวัติงานเดิม."""
    try:
        account = await update_staff_profile(
            session, staff_id=staff_id, payload=payload, actor=admin
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DuplicateStaffError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return StaffResponse.model_validate(account)


def _blocked_conflict(exc: StaffChangeBlockedError) -> HTTPException:
    """409 ที่แนบรายการงานค้าง เพื่อให้หน้า admin บอกได้ว่าต้องโอนงานไหนก่อน."""
    detail: str | dict[str, object] = str(exc)
    if exc.assignments:
        detail = {
            "message": str(exc),
            "unfinished_assignments": [
                {
                    "id": str(request.id),
                    "request_code": request.request_code,
                    "title": request.title,
                    "status": request.status.value,
                }
                for request in exc.assignments
            ],
        }
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


@router.patch("/{staff_id}/status", response_model=StaffResponse)
async def change_staff_status(
    staff_id: UUID, payload: StaffStatusUpdate, session: DbSession, admin: AdminStaff
) -> StaffResponse:
    """Admin ระงับหรือเปิดบัญชีคืน; บัญชีที่ถูกระงับจะ login และใช้ token เดิมไม่ได้ทันที."""
    try:
        account = await set_staff_status(
            session, staff_id=staff_id, new_status=payload.status, actor=admin
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except StaffActorNotAuthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except StaffChangeBlockedError as exc:
        raise _blocked_conflict(exc) from exc
    return StaffResponse.model_validate(account)


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(staff_id: UUID, session: DbSession, admin: AdminStaff) -> None:
    """Remove a staff account from active use while retaining historical records."""
    try:
        await delete_staff_account(session, staff_id=staff_id, deleted_by=admin)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except StaffActorNotAuthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except StaffChangeBlockedError as exc:
        raise _blocked_conflict(exc) from exc
