"""Schemas สำหรับ Repair Staff."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import PriorityLevel, RequestAction, RequestStatus


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


class AssignedTechnicianResponse(BaseModel):
    id: UUID
    staff_code: str
    full_name: str


class RepairTaskResponse(BaseModel):
    id: UUID
    request_code: str
    title: str
    status: str
    assigned_staff: AssignedTechnicianResponse


class RepairStatusUpdateRequest(BaseModel):
    status: RequestStatus


class RepairNoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=2000)

    @field_validator("note")
    @classmethod
    def validate_note(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Repair note must not be empty")

        return value


class RepairNoteResponse(BaseModel):
    id: UUID
    request_id: UUID
    note: str
    created_at: datetime


class RepairWorkHistoryItem(BaseModel):
    id: UUID
    action: RequestAction
    note: str | None
    old_status: RequestStatus | None
    new_status: RequestStatus | None
    created_at: datetime


class RepairWorkHistoryResponse(BaseModel):
    request_id: UUID
    history: list[RepairWorkHistoryItem]