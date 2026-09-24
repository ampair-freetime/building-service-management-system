"""Endpoints สำหรับ Cleaning Staff."""

from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.dependencies import DbSession, HousekeeperStaff, ObjectStorageClient
from app.schemas.cleaning_staff import (
    AssignedCleanerResponse,
    CleaningStatusUpdateRequest,
    CleaningTaskResponse,
    CleaningWorkHistoryItem,
    CleaningWorkHistoryResponse,
    CompletionNoteRequest,
    CompletionNoteResponse,
    CompletionPhotoResponse,
    CompletionPhotoUploadResponse,
)
from app.services.cleaning_staff import (
    CleaningTaskAlreadyAssignedError,
    CleaningTaskNotCompletedError,
    CleaningTaskNotFoundError,
    InvalidCleaningStatusTransitionError,
    accept_cleaning_task,
    add_completion_note,
    update_cleaning_task_status,
    upload_completion_photos,
    get_cleaning_work_history,
)
from app.services.images import InvalidImageError
from app.services.object_storage import StorageOperationError

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
            full_name=housekeeper.full_name,
        ),
    )


@router.patch(
    "/{request_id}/status",
    response_model=CleaningTaskResponse,
)
async def update_task_status(
    request_id: UUID,
    payload: CleaningStatusUpdateRequest,
    session: DbSession,
    housekeeper: HousekeeperStaff,
) -> CleaningTaskResponse:
    try:
        task = await update_cleaning_task_status(
            session,
            request_id=request_id,
            staff_id=housekeeper.id,
            new_status=payload.status,
        )
    except CleaningTaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except CleaningTaskAlreadyAssignedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except InvalidCleaningStatusTransitionError as exc:
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
            full_name=housekeeper.full_name,
        ),
    )


@router.post(
    "/{request_id}/completion-note",
    response_model=CompletionNoteResponse,
)
async def create_completion_note(
    request_id: UUID,
    payload: CompletionNoteRequest,
    session: DbSession,
    housekeeper: HousekeeperStaff,
) -> CompletionNoteResponse:
    try:
        history = await add_completion_note(
            session,
            request_id=request_id,
            staff_id=housekeeper.id,
            note=payload.note,
        )
    except CleaningTaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except CleaningTaskAlreadyAssignedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except CleaningTaskNotCompletedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return CompletionNoteResponse(
        id=history.id,
        request_id=history.request_id,
        note=history.note,
        created_at=history.created_at,
    )


@router.post(
    "/{request_id}/completion-photos",
    response_model=CompletionPhotoUploadResponse,
)
async def upload_task_completion_photos(
    request_id: UUID,
    session: DbSession,
    housekeeper: HousekeeperStaff,
    storage: ObjectStorageClient,
    files: list[UploadFile] = File(...),
) -> CompletionPhotoUploadResponse:
    try:
        images = await upload_completion_photos(
            session,
            request_id=request_id,
            staff_id=housekeeper.id,
            uploads=files,
            storage=storage,
        )
    except CleaningTaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except CleaningTaskAlreadyAssignedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except CleaningTaskNotCompletedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except InvalidImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except StorageOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ไม่สามารถอัปโหลดรูปภาพได้",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return CompletionPhotoUploadResponse(
        request_id=request_id,
        image_count=len(images),
        photos=[
            CompletionPhotoResponse(
                id=image.id,
                content_type=image.content_type,
                size_bytes=image.size_bytes,
                width=image.width,
                height=image.height,
                created_at=image.created_at,
            )
            for image in images
        ],
    )


@router.get(
    "/{request_id}/history",
    response_model=CleaningWorkHistoryResponse,
)
async def read_cleaning_work_history(
    request_id: UUID,
    session: DbSession,
    housekeeper: HousekeeperStaff,
) -> CleaningWorkHistoryResponse:
    try:
        history = await get_cleaning_work_history(
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return CleaningWorkHistoryResponse(
        request_id=request_id,
        history=[
            CleaningWorkHistoryItem(
                id=item.id,
                action=item.action,
                note=item.note,
                old_status=item.old_status,
                new_status=item.new_status,
                created_at=item.created_at,
            )
            for item in history
        ],
    )