"""Schemas สำหรับ Cleaning Staff."""

from uuid import UUID
from datetime import datetime

from pydantic import BaseModel
from app.models.enums import RequestStatus


class AssignedCleanerResponse(BaseModel):
    id: UUID
    staff_code: str
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