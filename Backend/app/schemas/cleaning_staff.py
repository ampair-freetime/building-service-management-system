"""Schemas สำหรับ Cleaning Staff."""

from uuid import UUID

from pydantic import BaseModel


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
