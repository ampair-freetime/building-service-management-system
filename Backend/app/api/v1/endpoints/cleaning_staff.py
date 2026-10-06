"""Endpoints สำหรับ Cleaning Staff."""

from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.dependencies import (
    DbSession,
    HousekeeperStaff,
    ObjectStorageClient,
    OptionalObjectStorageClient,
)
from app.schemas.cleaning_staff import (
    CleaningTaskDetailResponse,
    CleaningTaskImageResponse,
    CleaningTaskListItem,
    CleaningTaskListResponse,
    CleaningTaskLocationResponse,
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
    get_cleaning_task_detail,
    list_cleaning_tasks,
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

from app.models.enums import RequestType
from app.schemas.task_return import TaskReturnRequest, TaskReturnResponse
from app.services.task_return import (
    TaskNotFoundError,
    TaskNotOwnedError,
    TaskNotReturnableError,
    return_task_to_pool,
)

router = APIRouter()


def _location(task) -> CleaningTaskLocationResponse:
    return CleaningTaskLocationResponse(
        id=task.location.id, floor=task.location.floor, area=task.location.area
    )


@router.get("", response_model=CleaningTaskListResponse)
async def read_cleaning_tasks(
    session: DbSession,
    housekeeper: HousekeeperStaff,
) -> CleaningTaskListResponse:
    """งานที่ยังว่างให้รับ และงานที่แม่บ้านคนนี้รับไว้ สำหรับแสดงทันทีที่เปิด dashboard."""
    tasks = await list_cleaning_tasks(session, staff_id=housekeeper.id)
    return CleaningTaskListResponse(
        requests=[
            CleaningTaskListItem(
                id=task.id,
                request_code=task.request_code,
                title=task.title,
                description=task.description,
                cleaning_category=task.cleaning_category,
                priority=task.priority,
                status=task.status,
                location=_location(task),
                assigned_staff_id=task.assigned_staff_id,
                created_at=task.created_at,
            )
            for task in tasks
        ]
    )


@router.get("/{request_id}", response_model=CleaningTaskDetailResponse)
async def read_cleaning_task_detail(
    request_id: UUID,
    session: DbSession,
    housekeeper: HousekeeperStaff,
    storage: OptionalObjectStorageClient,
) -> CleaningTaskDetailResponse:
    try:
        task = await get_cleaning_task_detail(
            session, request_id=request_id, staff_id=housekeeper.id
        )
    except CleaningTaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    images = []
    # ไม่มี R2 config ก็ยังแสดงรายละเอียดงานได้ เพียงไม่มีรูป
    if storage is not None:
        images = [
            CleaningTaskImageResponse(
                id=image.id,
                image_type=image.image_type.value,
                content_type=image.content_type,
                size_bytes=image.size_bytes,
                width=image.width,
                height=image.height,
                sort_order=image.sort_order,
                url=storage.create_download_url(image.object_key),
                created_at=image.created_at,
            )
            for image in sorted(
                (image for image in task.images if image.deleted_at is None),
                key=lambda image: (
                    image.sort_order is None,
                    image.sort_order or 0,
                    image.created_at,
                ),
            )
        ]

    return CleaningTaskDetailResponse(
        id=task.id,
        request_code=task.request_code,
        title=task.title,
        description=task.description,
        cleaning_category=task.cleaning_category,
        priority=task.priority,
        status=task.status,
        reporter_email=task.reporter_email,
        location=_location(task),
        assigned_staff_id=task.assigned_staff_id,
        images=images,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
    )


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


@router.post(
    "/{request_id}/return",
    response_model=TaskReturnResponse,
)
async def return_task(
    request_id: UUID,
    payload: TaskReturnRequest,
    session: DbSession,
    housekeeper: HousekeeperStaff,
) -> TaskReturnResponse:
    """คืนงานที่ตัวเองรับไว้กลับเข้าคิวกลาง พร้อมบันทึกเหตุผลลงประวัติงาน."""
    try:
        task = await return_task_to_pool(
            session,
            request_id=request_id,
            request_type=RequestType.CLEANING,
            staff_id=housekeeper.id,
            reason=payload.reason,
            note=payload.note,
        )
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TaskNotOwnedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TaskNotReturnableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return TaskReturnResponse(
        id=task.id,
        request_code=task.request_code,
        title=task.title,
        status=task.status.value,
    )
