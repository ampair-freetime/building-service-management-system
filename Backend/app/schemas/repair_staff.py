"""Schemas สำหรับ Repair Staff."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import PriorityLevel, RequestStatus


class RepairRequestLocationResponse(BaseModel):
    id: int
    floor: str | None
    area: str


class RepairRequestListItem(BaseModel):
    id: UUID
    request_code: str
    title: str
    description: str
    priority: PriorityLevel
    status: RequestStatus
    location: RepairRequestLocationResponse
    assigned_staff_id: UUID | None
    created_at: datetime


class RepairRequestListResponse(BaseModel):
    requests: list[RepairRequestListItem]


class RepairRequestImageResponse(BaseModel):
    id: UUID
    image_type: str
    content_type: str | None
    size_bytes: int | None
    width: int | None
    height: int | None
    sort_order: int | None
    url: str
    created_at: datetime


class RepairRequestDetailResponse(BaseModel):
    id: UUID
    request_code: str
    title: str
    description: str
    priority: PriorityLevel
    status: RequestStatus
    reporter_email: str
    location: RepairRequestLocationResponse
    assigned_staff_id: UUID | None
    images: list[RepairRequestImageResponse]
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
