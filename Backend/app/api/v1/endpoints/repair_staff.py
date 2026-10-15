"""Endpoints สำหรับ Repair Staff (business logic อยู่ใน services/task_lifecycle.py)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies import (
    DbSession,
    ObjectStorageClient,
    OptionalObjectStorageClient,
    TechnicianStaff,
)
from app.api.v1.forms import parse_guest_image_uploads
from app.api.v1.task_http import task_http_errors, visible_images
from app.models.enums import RequestType
from app.models.service_request import ServiceRequest
from app.models.staff import Staff
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
from app.schemas.task_return import TaskReturnRequest, TaskReturnResponse
from app.services import task_lifecycle
from app.services.image_urls import build_image_url

REPAIR = RequestType.REPAIR

router = APIRouter()


def _location(task: ServiceRequest) -> RepairRequestLocationResponse:
    return RepairRequestLocationResponse(
        id=task.location.id, floor=task.location.floor, area=task.location.area
    )


def _task_response(task: ServiceRequest, technician: Staff) -> RepairTaskResponse:
    return RepairTaskResponse(
        id=task.id,
        request_code=task.request_code,
        title=task.title,
        status=task.status.value,
        assigned_staff=AssignedTechnicianResponse(
            id=technician.id, full_name=technician.full_name
        ),
    )


@router.get("", response_model=RepairRequestListResponse)
async def read_repair_requests(
    session: DbSession,
    technician: TechnicianStaff,
) -> RepairRequestListResponse:
    tasks = await task_lifecycle.list_tasks(
        session, request_type=REPAIR, staff_id=technician.id
    )
    reported_ids = await task_lifecycle.completion_report_ids(
        session, [task.id for task in tasks]
    )
    return RepairRequestListResponse(
        requests=[
            RepairRequestListItem(
                id=task.id,
                request_code=task.request_code,
                title=task.title,
                description=task.description,
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


@router.get("/{request_id}", response_model=RepairRequestDetailResponse)
async def read_repair_request_detail(
    request_id: UUID,
    session: DbSession,
    technician: TechnicianStaff,
    storage: OptionalObjectStorageClient,
) -> RepairRequestDetailResponse:
    with task_http_errors():
        task = await task_lifecycle.get_task_detail(
            session, request_type=REPAIR, request_id=request_id, staff_id=technician.id
        )

    images = []
    # ไม่มี R2 config ก็ยังแสดงรายละเอียดงานได้ เพียงไม่มีรูป
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
            for image in visible_images(task)
        ]

    return RepairRequestDetailResponse(
        id=task.id,
        request_code=task.request_code,
        title=task.title,
        description=task.description,
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


@router.patch("/{request_id}/accept", response_model=RepairTaskResponse)
async def accept_task(
    request_id: UUID,
    session: DbSession,
    technician: TechnicianStaff,
) -> RepairTaskResponse:
    with task_http_errors():
        task = await task_lifecycle.accept_task(
            session, request_type=REPAIR, request_id=request_id, staff_id=technician.id
        )
    return _task_response(task, technician)


@router.patch("/{request_id}/status", response_model=RepairTaskResponse)
async def update_task_status(
    request_id: UUID,
    payload: RepairStatusUpdateRequest,
    session: DbSession,
    technician: TechnicianStaff,
) -> RepairTaskResponse:
    with task_http_errors():
        task = await task_lifecycle.advance_task_status(
            session,
            request_type=REPAIR,
            request_id=request_id,
            staff_id=technician.id,
            new_status=payload.status,
        )
    return _task_response(task, technician)


@router.post("/{request_id}/completion-note", response_model=RepairNoteResponse)
async def add_completion_note(
    request_id: UUID,
    payload: RepairNoteRequest,
    session: DbSession,
    technician: TechnicianStaff,
) -> RepairNoteResponse:
    with task_http_errors():
        history = await task_lifecycle.add_completion_note(
            session,
            request_type=REPAIR,
            request_id=request_id,
            staff_id=technician.id,
            note=payload.note,
        )
    return RepairNoteResponse(
        id=history.id,
        request_id=history.request_id,
        note=history.note,
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
    files: Annotated[list[UploadFile], File()],
) -> RepairCompletionPhotoUploadResponse:
    with task_http_errors():
        images = await task_lifecycle.upload_completion_photos(
            session,
            request_type=REPAIR,
            request_id=request_id,
            staff_id=technician.id,
            uploads=files,
            storage=storage,
        )
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


@router.get("/{request_id}/history", response_model=RepairWorkHistoryResponse)
async def get_work_history(
    request_id: UUID,
    session: DbSession,
    technician: TechnicianStaff,
) -> RepairWorkHistoryResponse:
    with task_http_errors():
        history = await task_lifecycle.get_work_history(
            session, request_type=REPAIR, request_id=request_id, staff_id=technician.id
        )
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


@router.post("/{request_id}/return", response_model=TaskReturnResponse)
async def return_task(
    request_id: UUID,
    payload: TaskReturnRequest,
    session: DbSession,
    technician: TechnicianStaff,
) -> TaskReturnResponse:
    """คืนงานที่ตัวเองรับไว้กลับเข้าคิวกลาง พร้อมบันทึกเหตุผลลงประวัติงาน."""
    with task_http_errors():
        task = await task_lifecycle.return_task_to_pool(
            session,
            request_type=REPAIR,
            request_id=request_id,
            staff_id=technician.id,
            reason=payload.reason,
            note=payload.note,
        )
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
) -> RepairTaskResponse:
    with task_http_errors():
        task = await task_lifecycle.complete_task_with_report(
            session,
            request_type=REPAIR,
            request_id=request_id,
            staff_id=staff.id,
            note=note,
            uploads=images,
            storage=storage,
        )
    return _task_response(task, staff)
