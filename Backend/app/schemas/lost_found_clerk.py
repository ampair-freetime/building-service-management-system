from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator
from app.models.enums import ClaimStatus, LostStatus, LostType


class PendingFoundItemResponse(BaseModel):
    """ข้อมูลของที่พบซึ่งรอเจ้าหน้าที่ธุรการตรวจสอบ"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_code: str
    report_type: LostType
    item_name: str
    description: str | None
    location_detail: str | None
    status: LostStatus
    created_at: datetime


class PendingLostItemResponse(BaseModel):
    """ข้อมูลประกาศของหายซึ่งรอเจ้าหน้าที่ธุรการตรวจสอบ"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_code: str
    report_type: LostType
    item_name: str
    description: str | None
    location_detail: str | None
    status: LostStatus
    created_at: datetime


class FoundItemDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_code: str
    report_type: LostType
    item_category: str
    item_name: str
    description: str | None
    event_datetime: datetime
    location_detail: str | None
    custody_location: str | None
    reporter_email: str
    status: LostStatus
    created_at: datetime


class LostItemDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_code: str
    report_type: LostType
    item_category: str
    item_name: str
    description: str | None
    event_datetime: datetime
    location_detail: str | None
    reporter_email: str
    status: LostStatus
    created_at: datetime


class RejectFoundItemRequest(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Rejection reason is required")

        return value


class OwnershipRequestListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    found_item_id: UUID
    claimant_name: str
    claimant_email: str
    status: ClaimStatus
    created_at: datetime


class OwnershipRequestDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    found_item_id: UUID

    # Claimant information
    claimant_name: str
    claimant_email: str

    # Ownership evidence
    proof_detail: str

    # Request information
    status: ClaimStatus
    review_note: str | None
    created_at: datetime
    updated_at: datetime

    # Item information
    item_code: str
    item_name: str
    item_category: str
    description: str | None
    location_detail: str | None
    custody_location: str | None
    

class RequestAdditionalInfoRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Additional information request message is required")

        return value
