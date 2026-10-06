"""Read models for the administrator's cleaning and repair workload overview."""

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AccountStatus, RequestAction, RequestStatus, RequestType, StaffRole
from app.models.service_request import RequestHistory, ServiceRequest
from app.models.staff import Staff
from app.schemas.staff_work_overview import (
    CurrentWorkItem,
    ReturnedWorkItem,
    StaffCurrentWorkResponse,
    StaffWorkCounts,
    StaffWorkOverviewItem,
    StaffWorkOverviewResponse,
    StaffWorkOverviewSummary,
    StaffWorkRoleFilter,
)

_OPEN_STATUSES = (
    RequestStatus.WAITING,
    RequestStatus.ASSIGNED,
    RequestStatus.RECEIVED,
    RequestStatus.IN_PROGRESS,
)
_WORKER_ROLES = (StaffRole.HOUSEKEEPER, StaffRole.TECHNICIAN)


class OverviewStaffNotFoundError(LookupError):
    """The requested account is not an active cleaning or repair staff member."""


def _request_type_for_role(role: StaffWorkRoleFilter | None) -> RequestType | None:
    if role == "cleaning":
        return RequestType.CLEANING
    if role == "repair":
        return RequestType.REPAIR
    return None


def _staff_role_for_role(role: StaffWorkRoleFilter | None) -> StaffRole | None:
    if role == "cleaning":
        return StaffRole.HOUSEKEEPER
    if role == "repair":
        return StaffRole.TECHNICIAN
    return None


async def _counts_by_staff(
    session: AsyncSession,
    *,
    staff_ids: Iterable[UUID],
    action: RequestAction | None = None,
) -> dict[UUID, int]:
    ids = list(staff_ids)
    if not ids:
        return {}

    if action is None:
        statement = (
            select(ServiceRequest.assigned_staff_id, func.count(ServiceRequest.id))
            .where(
                ServiceRequest.assigned_staff_id.in_(ids),
                ServiceRequest.status.in_(_OPEN_STATUSES),
            )
            .group_by(ServiceRequest.assigned_staff_id)
        )
    else:
        statement = (
            select(RequestHistory.performed_by, func.count(func.distinct(RequestHistory.request_id)))
            .join(ServiceRequest, ServiceRequest.id == RequestHistory.request_id)
            .where(
                RequestHistory.performed_by.in_(ids),
                RequestHistory.action == action,
                ServiceRequest.request_type.in_((RequestType.CLEANING, RequestType.REPAIR)),
            )
            .group_by(RequestHistory.performed_by)
        )
    return {staff_id: count for staff_id, count in (await session.execute(statement)).all()}


async def get_staff_work_overview(
    session: AsyncSession, *, role: StaffWorkRoleFilter | None, search: str | None
) -> StaffWorkOverviewResponse:
    """Return filtered worker statistics and matching overall figures for an admin."""
    staff_filters = [
        Staff.status == AccountStatus.ACTIVE,
        Staff.role.in_(_WORKER_ROLES),
    ]
    selected_role = _staff_role_for_role(role)
    if selected_role is not None:
        staff_filters.append(Staff.role == selected_role)
    if search and search.strip():
        needle = f"%{search.strip()}%"
        staff_filters.append(Staff.full_name.ilike(needle) | Staff.email.ilike(needle))

    staff = list(
        await session.scalars(select(Staff).where(*staff_filters).order_by(Staff.full_name, Staff.email))
    )
    staff_ids = [account.id for account in staff]
    current = await _counts_by_staff(session, staff_ids=staff_ids)
    closed = await _counts_by_staff(
        session, staff_ids=staff_ids, action=RequestAction.COMPLETED
    )
    returned = await _counts_by_staff(
        session, staff_ids=staff_ids, action=RequestAction.RETURNED
    )

    request_filters = [
        ServiceRequest.assigned_staff_id.is_(None),
        ServiceRequest.status.in_(_OPEN_STATUSES),
    ]
    request_type = _request_type_for_role(role)
    if request_type is not None:
        request_filters.append(ServiceRequest.request_type == request_type)
    unassigned = await session.scalar(select(func.count()).select_from(ServiceRequest).where(*request_filters))

    rows = [
        StaffWorkOverviewItem(
            id=account.id,
            full_name=account.full_name,
            email=account.email,
            role=account.role,
            counts=StaffWorkCounts(
                current_assigned=current.get(account.id, 0),
                closed=closed.get(account.id, 0),
                returned=returned.get(account.id, 0),
            ),
        )
        for account in staff
    ]
    return StaffWorkOverviewResponse(
        summary=StaffWorkOverviewSummary(
            current_assigned=sum(item.counts.current_assigned for item in rows),
            closed=sum(item.counts.closed for item in rows),
            returned=sum(item.counts.returned for item in rows),
            unassigned=unassigned or 0,
        ),
        staff=rows,
    )


async def get_staff_current_work(
    session: AsyncSession, *, staff_id: UUID
) -> StaffCurrentWorkResponse:
    """Return only open requests still assigned to the selected worker."""
    staff = await session.scalar(
        select(Staff).where(
            Staff.id == staff_id,
            Staff.status == AccountStatus.ACTIVE,
            Staff.role.in_(_WORKER_ROLES),
        )
    )
    if staff is None:
        raise OverviewStaffNotFoundError("Cleaning or repair staff member not found")
    work = list(
        await session.scalars(
            select(ServiceRequest)
            .where(
                ServiceRequest.assigned_staff_id == staff.id,
                ServiceRequest.status.in_(_OPEN_STATUSES),
            )
            .order_by(ServiceRequest.created_at.desc(), ServiceRequest.id.desc())
        )
    )
    returned = (await session.execute(
        select(RequestHistory, ServiceRequest)
        .join(ServiceRequest, ServiceRequest.id == RequestHistory.request_id)
        .where(RequestHistory.performed_by == staff.id,
               RequestHistory.action == RequestAction.RETURNED,
               ServiceRequest.request_type.in_((RequestType.CLEANING, RequestType.REPAIR)))
        .order_by(RequestHistory.created_at.desc(), RequestHistory.id.desc())
    )).all()
    return StaffCurrentWorkResponse(
        staff_id=staff.id,
        full_name=staff.full_name,
        current_work_count=len(work),
        current_work=[CurrentWorkItem.model_validate(request) for request in work],
        returned_work=[ReturnedWorkItem(
            id=request.id, request_code=request.request_code,
            request_type=request.request_type, title=request.title, status=request.status,
            history_id=history.id, reason=history.note, returned_at=history.created_at,
            returned_by=staff.full_name,
        ) for history, request in returned],
    )
