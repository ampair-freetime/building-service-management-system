"""Endpoints สำหรับ Cleaning Staff (business logic อยู่ใน services/task_lifecycle.py)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies import (
    DbSession,
    HousekeeperStaff,
    ObjectStorageClient,
    OptionalObjectStorageClient,
)
from app.api.v1.forms import parse_guest_image_uploads
from app.api.v1.task_http import task_http_errors, visible_images
from app.models.enums import RequestType
from app.schemas.cleaning_staff import (
    AssignedCleanerResponse,
    CleaningStatusUpdateRequest,
    CleaningTaskDetailResponse,
    CleaningTaskImageResponse,
    CleaningTaskListItem,
    CleaningTaskListResponse,
    CleaningTaskLocationResponse,
    CleaningTaskResponse,
    CleaningWorkHistoryItem,
    CleaningWorkHistoryResponse,
    CompletionNoteRequest,
    CompletionNoteResponse,
    CompletionPhotoResponse,
    CompletionPhotoUploadResponse,
)
from app.schemas.task_return import TaskReturnRequest, TaskReturnResponse
from app.services import task_lifecycle
from app.services.image_urls import build_image_url

CLEANING = RequestType.CLEANING

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
    tasks = await task_lifecycle.list_tasks(
        session, request_type=CLEANING, staff_id=housekeeper.id
    )
    reported_ids = await task_lifecycle.completion_report_ids(session, [item.id for item in tasks])
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
                has_completion_report=task.id in reported_ids,
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
    with task_http_errors():
        task = await task_lifecycle.get_task_detail(
            session, request_type=CLEANING, request_id=request_id, staff_id=housekeeper.id
        )

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
                url=build_image_url(image.id),
                created_at=image.created_at,
            )
            for image in visible_images(task)
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
    with task_http_errors():
        task = await task_lifecycle.accept_task(
            session,
            request_type=CLEANING,
            request_id=request_id,
            staff_id=housekeeper.id,
        )

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
    with task_http_errors():
        task = await task_lifecycle.advance_task_status(
            session,
            request_type=CLEANING,
            request_id=request_id,
            staff_id=housekeeper.id,
            new_status=payload.status,
        )

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
    with task_http_errors():
        history = await task_lifecycle.add_completion_note(
            session,
            request_type=CLEANING,
            request_id=request_id,
            staff_id=housekeeper.id,
            note=payload.note,
        )

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
    files: Annotated[list[UploadFile], File()],
) -> CompletionPhotoUploadResponse:
    with task_http_errors():
        images = await task_lifecycle.upload_completion_photos(
            session,
            request_type=CLEANING,
            request_id=request_id,
            staff_id=housekeeper.id,
            uploads=files,
            storage=storage,
        )

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
    with task_http_errors():
        history = await task_lifecycle.get_work_history(
            session,
            request_type=CLEANING,
            request_id=request_id,
            staff_id=housekeeper.id,
        )

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
    with task_http_errors():
        task = await task_lifecycle.return_task_to_pool(
            session,
            request_type=CLEANING,
            request_id=request_id,
            staff_id=housekeeper.id,
            reason=payload.reason,
            note=payload.note,
        )

    return TaskReturnResponse(
        id=task.id,
        request_code=task.request_code,
        title=task.title,
        status=task.status.value,
    )


@router.post("/{request_id}/complete", response_model=CleaningTaskResponse)
async def complete_task(
    request_id: UUID,
    session: DbSession,
    staff: HousekeeperStaff,
    storage: OptionalObjectStorageClient,
    note: Annotated[str, Form(min_length=1, max_length=2000)],
    images: Annotated[list[UploadFile], Depends(parse_guest_image_uploads)],
):
    with task_http_errors():
        task = await task_lifecycle.complete_task_with_report(
            session,
            request_type=CLEANING,
            request_id=request_id,
            staff_id=staff.id,
            note=note,
            uploads=images,
            storage=storage,
        )
    return CleaningTaskResponse(
        id=task.id, request_code=task.request_code, title=task.title,
        status=task.status.value,
        assigned_staff=AssignedCleanerResponse(id=staff.id, full_name=staff.full_name),
    )
