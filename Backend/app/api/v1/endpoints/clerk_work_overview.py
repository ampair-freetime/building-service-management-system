"""Admin endpoints for monitoring clerk approval activity."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import AdminStaff, DbSession
from app.models.enums import LostType
from app.schemas.clerk_work_overview import (
    ClerkAnnouncementListResponse,
    ClerkApprovalMetric,
    ClerkWorkOverviewResponse,
)
from app.services.clerk_work_overview import (
    get_clerk_work_overview,
    list_clerk_work_announcements,
)

router = APIRouter()


@router.get("", response_model=ClerkWorkOverviewResponse)
async def read_clerk_work_overview(
    session: DbSession,
    _admin: AdminStaff,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    announcement_type: Annotated[LostType | None, Query()] = None,
) -> ClerkWorkOverviewResponse:
    """Get statistics using inclusive UTC calendar-date filters."""
    _validate_date_range(date_from, date_to)
    return await get_clerk_work_overview(
        session,
        date_from=date_from,
        date_to=date_to,
        announcement_type=announcement_type,
    )


@router.get("/announcements", response_model=ClerkAnnouncementListResponse)
async def read_clerk_work_announcements(
    session: DbSession,
    _admin: AdminStaff,
    metric: Annotated[ClerkApprovalMetric, Query()],
    announcement_type: Annotated[LostType | None, Query()] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> ClerkAnnouncementListResponse:
    """Drill into the announcements counted by a selected dashboard metric."""
    _validate_date_range(date_from, date_to)
    return await list_clerk_work_announcements(
        session,
        metric=metric,
        announcement_type=announcement_type,
        date_from=date_from,
        date_to=date_to,
    )


def _validate_date_range(date_from: date | None, date_to: date | None) -> None:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="date_from must be on or before date_to",
        )
