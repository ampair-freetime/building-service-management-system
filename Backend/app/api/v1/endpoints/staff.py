"""API endpoints สำหรับให้แอดมินสร้างและดูบัญชีพนักงาน."""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AdminStaff, DbSession
from app.schemas.staff import StaffCreate, StaffResponse
from app.services.staff import DuplicateStaffError, create_staff, list_staff

router = APIRouter()


@router.get("", response_model=list[StaffResponse])
async def read_staff(session: DbSession, _admin: AdminStaff) -> list[StaffResponse]:
    """แสดงบัญชีพนักงานทั้งหมด โดย FastAPI ตรวจสิทธิ์ admin ก่อนเรียกฟังก์ชัน."""
    accounts = await list_staff(session)
    return [StaffResponse.model_validate(account) for account in accounts]


@router.post("", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def add_staff(
    payload: StaffCreate, session: DbSession, _admin: AdminStaff
) -> StaffResponse:
    """สร้างบัญชีพนักงานใหม่ โดยอนุญาตเฉพาะ admin."""
    try:
        account = await create_staff(session, payload)
    except DuplicateStaffError as exc:
        # HTTP 409 หมายถึงข้อมูลใหม่ขัดแย้งกับบัญชีที่มีอยู่แล้ว
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return StaffResponse.model_validate(account)
