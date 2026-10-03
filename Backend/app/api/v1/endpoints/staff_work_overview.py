"""Admin APIs for monitoring cleaning and repair staff workload."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import AdminStaff, DbSession
from app.schemas.staff_work_overview import (
    StaffCurrentWorkResponse,
    StaffWorkOverviewResponse,
    StaffWorkRoleFilter,
)
from app.services.staff_work_overview import (
    OverviewStaffNotFoundError,
    get_staff_current_work,
    get_staff_work_overview,
)

router = APIRouter()


@router.get("", response_model=StaffWorkOverviewResponse)
async def read_staff_work_overview(
    session: DbSession,
    _admin: AdminStaff,
    role: Annotated[StaffWorkRoleFilter | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=150)] = None,
) -> StaffWorkOverviewResponse:
    return await get_staff_work_overview(session, role=role, search=search)


@router.get("/{staff_id}/current-work", response_model=StaffCurrentWorkResponse)
async def read_staff_current_work(
    staff_id: UUID, session: DbSession, _admin: AdminStaff
) -> StaffCurrentWorkResponse:
    try:
        return await get_staff_current_work(session, staff_id=staff_id)
    except OverviewStaffNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
