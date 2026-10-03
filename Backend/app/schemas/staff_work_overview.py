"""Response contracts for the admin staff-work overview."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import RequestStatus, RequestType, StaffRole


class StaffWorkCounts(BaseModel):
    current_assigned: int
    closed: int
    returned: int


class StaffWorkOverviewItem(BaseModel):
    id: UUID
    full_name: str
    email: str
    role: StaffRole
    counts: StaffWorkCounts


class StaffWorkOverviewSummary(StaffWorkCounts):
    unassigned: int


class StaffWorkOverviewResponse(BaseModel):
    summary: StaffWorkOverviewSummary
    staff: list[StaffWorkOverviewItem]


class CurrentWorkItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_code: str
    request_type: RequestType
    title: str
    status: RequestStatus


class StaffCurrentWorkResponse(BaseModel):
    staff_id: UUID
    full_name: str
    current_work_count: int
    current_work: list[CurrentWorkItem]


StaffWorkRoleFilter = Literal["cleaning", "repair"]
