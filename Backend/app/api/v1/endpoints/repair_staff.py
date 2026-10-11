"""Endpoints สำหรับ Repair Staff."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, File, HTTPException, UploadFile, status

from app.api.dependencies import (
    DbSession,
    ObjectStorageClient,
    OptionalObjectStorageClient,
    TechnicianStaff,
)
from app.schemas.repair_staff import (
    AssignedTechnicianResponse,
    RepairCompletionPhotoResponse,
    RepairCompletionPhotoUploadResponse,
    RepairNoteRequest,
    RepairNoteResponse,
    RepairRequestDetailResponse,
    RepairRequestImageResponse,
    RepairRequestListItem,
    RepairRequestListResponse,
    RepairRequestLocationResponse,
    RepairStatusUpdateRequest,
    RepairTaskResponse,
    RepairWorkHistoryItem,
    RepairWorkHistoryResponse,
)
from app.services.image_urls import build_image_url
from app.services.images import InvalidImageError
from app.services.object_storage import StorageOperationError
from app.services.repair_staff import (
    InvalidRepairStatusTransitionError,
    RepairRequestNotFoundError,
    RepairTaskAlreadyAssignedError,
    RepairTaskNotCompletedError,
    accept_repair_task,
    add_repair_completion_note,
    get_repair_request_detail,
    get_repair_work_history,
    list_repair_requests,
    update_repair_task_status,
    upload_repair_completion_photos,
)

from app.models.enums import RequestType
from app.schemas.task_return import TaskReturnRequest, TaskReturnResponse
from app.services.task_return import (
    TaskNotFoundError,
    TaskNotOwnedError,
    TaskNotReturnableError,
    return_task_to_pool,
)

from app.api.v1.forms import parse_guest_image_uploads
from app.services.task_completion import (
    complete_task_with_report, completion_report_ids, CompletionNotFoundError,
    CompletionNotOwnedError, CompletionConflictError,
)

router = APIRouter()


@router.get(
    "",
    response_model=RepairRequestListResponse,
)
async def read_repair_requests(
    session: DbSession,
    technician: TechnicianStaff,
) -> RepairRequestListResponse:
    requests = await list_repair_requests(session)

    reported_ids = await completion_report_ids(session, [item.id for item in requests])
    return RepairRequestListResponse(
        requests=[
            RepairRequestListItem(
                id=request.id,
                request_code=request.request_code,
                title=request.title,
                description=request.description,
                priority=request.priority,
                status=request.status,
                location=RepairRequestLocationResponse(
                    id=request.location.id,
                    floor=request.location.floor,
                    area=request.location.area,
                ),
                assigned_staff_id=request.assigned_staff_id,
                created_at=request.created_at,
                has_completion_report=request.id in reported_ids,
            )
            for request in requests
        ]
    )


@router.get(
    "/{request_id}",
    response_model=RepairRequestDetailResponse,
)
async def read_repair_request_detail(
    request_id: UUID,
    session: DbSession,
    technician: TechnicianStaff,
    storage: OptionalObjectStorageClient,
) -> RepairRequestDetailResponse:
    try:
        request = await get_repair_request_detail(
            session,
            request_id,
        )
    except RepairRequestNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    images = []

    if storage is not None:
        images = [
            RepairRequestImageResponse(
                id=image.id,
                image_type=image.image_type.value,
                content_type=image.content_type,
                size_bytes=image.size_bytes,
                width=image.width,
                height=image.height,
                sort_order=image.sort_order,
                url=build_image_url(image.id),
                created_at=image.created_at,
            )
            for image in sorted(
                (image for image in request.images if image.deleted_at is None),
                key=lambda image: (
                    image.sort_order is None,
                    image.sort_order or 0,
                    image.created_at,
                ),
            )
        ]

    return RepairRequestDetailResponse(
        id=request.id,
        request_code=request.request_code,
        title=request.title,
        description=request.description,
        priority=request.priority,
        status=request.status,
        reporter_email=request.reporter_email,
        location=RepairRequestLocationResponse(
            id=request.location.id,
            floor=request.location.floor,
            area=request.location.area,
        ),
        assigned_staff_id=request.assigned_staff_id,
        images=images,
        created_at=request.created_at,
        updated_at=request.updated_at,
        completed_at=request.completed_at,
    )


@router.patch(
    "/{request_id}/accept",
    response_model=RepairTaskResponse,
)
async def accept_task(
    request_id: UUID,
    session: DbSession,
    technician: TechnicianStaff,
) -> RepairTaskResponse:
    try:
        task = await accept_repair_task(
            session,
            request_id=request_id,
            staff_id=technician.id,
        )
    except RepairRequestNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except RepairTaskAlreadyAssignedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return RepairTaskResponse(
        id=task.id,
        request_code=task.request_code,
        title=task.title,
        status=task.status.value,
        assigned_staff=AssignedTechnicianResponse(
            id=technician.id,
            full_name=technician.full_name,
        ),
    )


@router.patch(
    "/{request_id}/status",
    response_model=RepairTaskResponse,
)
async def update_task_status(
    request_id: UUID,
    payload: RepairStatusUpdateRequest,
    session: DbSession,
    technician: TechnicianStaff,
) -> RepairTaskResponse:
    try:
        task = await update_repair_task_status(
            session,
            request_id=request_id,
            staff_id=technician.id,
            new_status=payload.status,
        )
    except RepairRequestNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except RepairTaskAlreadyAssignedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except InvalidRepairStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return RepairTaskResponse(
        id=task.id,
        request_code=task.request_code,
        title=task.title,
        status=task.status.value,
        assigned_staff=AssignedTechnicianResponse(
            id=technician.id,
            full_name=technician.full_name,
        ),
    )


@router.post(
    "/{request_id}/completion-note",
    response_model=RepairNoteResponse,
)
async def add_completion_note(
    request_id: UUID,
    payload: RepairNoteRequest,
    session: DbSession,
    technician: TechnicianStaff,
) -> RepairNoteResponse:
    try:
        history = await add_repair_completion_note(
            session,
            request_id=request_id,
            staff_id=technician.id,
            note=payload.note,
        )
    except RepairRequestNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except RepairTaskAlreadyAssignedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except RepairTaskNotCompletedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return RepairNoteResponse(
        id=history.id,
        request_id=history.request_id,
        note=history.note or "",
        created_at=history.created_at,
    )


@router.post(
    "/{request_id}/completion-photos",
    response_model=RepairCompletionPhotoUploadResponse,
)
async def upload_task_completion_photos(
    request_id: UUID,
    session: DbSession,
    technician: TechnicianStaff,
    storage: ObjectStorageClient,
    files: list[UploadFile] = File(...),  # noqa: B008 - FastAPI dependency declaration
) -> RepairCompletionPhotoUploadResponse:
    try:
        images = await upload_repair_completion_photos(
            session,
            request_id=request_id,
            staff_id=technician.id,
            uploads=files,
            storage=storage,
        )
    except RepairRequestNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RepairTaskAlreadyAssignedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RepairTaskNotCompletedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except StorageOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ไม่สามารถอัปโหลดรูปภาพได้",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return RepairCompletionPhotoUploadResponse(
        request_id=request_id,
        image_count=len(images),
        photos=[
            RepairCompletionPhotoResponse(
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
    response_model=RepairWorkHistoryResponse,
)
async def get_work_history(
    request_id: UUID,
    session: DbSession,
    technician: TechnicianStaff,
) -> RepairWorkHistoryResponse:
    try:
        history = await get_repair_work_history(
            session,
            request_id=request_id,
            staff_id=technician.id,
        )
    except RepairRequestNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except RepairTaskAlreadyAssignedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return RepairWorkHistoryResponse(
        request_id=request_id,
        history=[
            RepairWorkHistoryItem(
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
    technician: TechnicianStaff,
) -> TaskReturnResponse:
    """คืนงานที่ตัวเองรับไว้กลับเข้าคิวกลาง พร้อมบันทึกเหตุผลลงประวัติงาน."""
    try:
        task = await return_task_to_pool(
            session,
            request_id=request_id,
            request_type=RequestType.REPAIR,
            staff_id=technician.id,
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


@router.post("/{request_id}/complete", response_model=RepairTaskResponse)
@router.patch("/{request_id}/complete", response_model=RepairTaskResponse)
async def complete_task(
    request_id: UUID,
    session: DbSession,
    staff: TechnicianStaff,
    storage: OptionalObjectStorageClient,
    note: Annotated[str, Form(min_length=1, max_length=2000)],
    images: Annotated[list[UploadFile], Depends(parse_guest_image_uploads)],
):
    try:
        task = await complete_task_with_report(
            session, request_id=request_id, request_type=RequestType.REPAIR,
            staff_id=staff.id, note=note, uploads=images, storage=storage,
        )
    except CompletionNotFoundError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except CompletionNotOwnedError as exc:
        raise HTTPException(403, detail=str(exc)) from exc
    except CompletionConflictError as exc:
        raise HTTPException(409, detail=str(exc)) from exc
    except (InvalidImageError, ValueError) as exc:
        raise HTTPException(422, detail=str(exc)) from exc
    except StorageOperationError as exc:
        raise HTTPException(502, detail="ไม่สามารถอัปโหลดรูปภาพได้") from exc
    return RepairTaskResponse(
        id=task.id, request_code=task.request_code, title=task.title,
        status=task.status.value,
        assigned_staff=AssignedTechnicianResponse(id=staff.id, full_name=staff.full_name),
    )
