"""Schemas สำหรับ Cleaning Staff."""

from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from app.models.enums import PriorityLevel, RequestAction, RequestStatus


class AssignedCleanerResponse(BaseModel):
    id: UUID
    full_name: str


class CleaningTaskResponse(BaseModel):
    id: UUID
    request_code: str
    title: str
    status: str
    assigned_staff: AssignedCleanerResponse


class CleaningStatusUpdateRequest(BaseModel):
    status: RequestStatus


class CompletionPhotoResponse(BaseModel):
    id: UUID
    content_type: str
    size_bytes: int
    width: int
    height: int
    created_at: datetime


class CompletionPhotoUploadResponse(BaseModel):
    request_id: UUID
    image_count: int
    photos: list[CompletionPhotoResponse]


class CompletionNoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=2000)

    @field_validator("note")
    @classmethod
    def validate_note(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Completion note must not be empty")

        return value


class CompletionNoteResponse(BaseModel):
    id: UUID
    request_id: UUID
    note: str
    created_at: datetime


class CleaningWorkHistoryItem(BaseModel):
    id: UUID
    action: RequestAction
    note: str | None
    old_status: RequestStatus | None
    new_status: RequestStatus | None
    created_at: datetime


class CleaningWorkHistoryResponse(BaseModel):
    request_id: UUID
    history: list[CleaningWorkHistoryItem]


class CleaningTaskLocationResponse(BaseModel):
    id: int
    floor: str | None
    area: str


class CleaningTaskListItem(BaseModel):
    """ข้อมูลการ์ดงานใน dashboard ของแม่บ้าน (รูปแบบเดียวกับ RepairRequestListItem)."""

    id: UUID
    request_code: str
    title: str
    description: str
    cleaning_category: str | None = None
    priority: PriorityLevel
    status: RequestStatus
    location: CleaningTaskLocationResponse
    assigned_staff_id: UUID | None
    created_at: datetime


class CleaningTaskListResponse(BaseModel):
    requests: list[CleaningTaskListItem]


class CleaningTaskImageResponse(BaseModel):
    id: UUID
    image_type: str
    content_type: str | None
    size_bytes: int | None
    width: int | None
    height: int | None
    sort_order: int | None
    url: str
    created_at: datetime


class CleaningTaskDetailResponse(BaseModel):
    id: UUID
    request_code: str
    title: str
    description: str
    cleaning_category: str | None = None
    priority: PriorityLevel
    status: RequestStatus
    reporter_email: str
    location: CleaningTaskLocationResponse
    assigned_staff_id: UUID | None
    images: list[CleaningTaskImageResponse]
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
