"""Endpoints สำหรับ Repair Staff."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import (
    DbSession,
    OptionalObjectStorageClient,
    TechnicianStaff,
)
from app.schemas.repair_staff import (
    RepairRequestDetailResponse,
    RepairRequestImageResponse,
    RepairRequestListItem,
    RepairRequestListResponse,
    RepairRequestLocationResponse,
)
from app.services.repair_staff import (
    RepairRequestNotFoundError,
    get_repair_request_detail,
    list_repair_requests,
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
                url=storage.create_download_url(image.object_key),
                created_at=image.created_at,
            )
            for image in sorted(
                (
                    image
                    for image in request.images
                    if image.deleted_at is None
                ),
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