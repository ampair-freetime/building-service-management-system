"""Response contracts for the admin clerk-approval overview."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ClaimStatus, LostStatus, LostType, ReturnStatus


class AnnouncementStatistics(BaseModel):
    total: int
    approved: int
    rejected: int
    pending_review: int
    oldest_pending_review_age_hours: float | None
    average_pending_review_age_hours: float | None


class ClerkClaimOverviewItem(BaseModel):
    id: UUID
    claim_code: str
    item_name: str
    claimant_name: str
    claimant_email: str
    status: ClaimStatus
    return_status: ReturnStatus | None
    proof_detail: str
    staff_message: str | None
    submission_date: datetime
    updated_at: datetime


class ClerkWorkOverviewResponse(BaseModel):
    """Aggregate approval counts across every clerk."""

    summary: AnnouncementStatistics
    by_announcement_type: dict[LostType, AnnouncementStatistics]
    date_from: date | None
    date_to: date | None
    announcement_type: LostType | None
    claims: list[ClerkClaimOverviewItem]


class ClerkAnnouncementListItem(BaseModel):
    id: UUID
    item_code: str
    announcement_type: LostType
    submission_date: datetime
    status: LostStatus
    pending_review_age_hours: float | None


class ClerkAnnouncementListResponse(BaseModel):
    metric: Literal["total", "approved", "rejected", "pending_review"]
    announcement_type: LostType | None
    date_from: date | None
    date_to: date | None
    total: int
    announcements: list[ClerkAnnouncementListItem]


ClerkApprovalMetric = Literal["total", "approved", "rejected", "pending_review"]
