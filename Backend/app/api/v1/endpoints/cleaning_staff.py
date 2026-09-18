"""Endpoints สำหรับ Cleaning Staff."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DbSession, HousekeeperStaff
from app.schemas.cleaning_staff import (
    AssignedCleanerResponse,
    CleaningTaskResponse,
)
from app.services.cleaning_staff import (
    CleaningTaskAlreadyAssignedError,
    CleaningTaskNotFoundError,
    accept_cleaning_task,
)

router = APIRouter()


@router.patch(
    "/{request_id}/accept",
    response_model=CleaningTaskResponse,
)
async def accept_task(
    request_id: UUID,
    session: DbSession,
    housekeeper: HousekeeperStaff,
) -> CleaningTaskResponse:
    try:
        task = await accept_cleaning_task(
            session,
            request_id=request_id,
            staff_id=housekeeper.id,
        )
    except CleaningTaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except CleaningTaskAlreadyAssignedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return CleaningTaskResponse(
        id=task.id,
        request_code=task.request_code,
        title=task.title,
        status=task.status.value,
        assigned_staff=AssignedCleanerResponse(
            id=housekeeper.id,
            staff_code=housekeeper.staff_code,
            full_name=housekeeper.full_name,
        ),
    )
