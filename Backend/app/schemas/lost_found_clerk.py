from datetime import datetime, time
from zoneinfo import ZoneInfo
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.models.enums import ClaimStatus, LostStatus, LostType, ReturnStatus
from app.schemas.lost_found_item import GuestImageResponse


# รูปให้ staff ตรวจก่อนอนุมัติ ส่งเป็น signed URL อายุสั้น โดย endpoint เติมค่าเองภายหลัง
# validation_alias ชี้ไปชื่อที่ LostItem ไม่มี เพื่อกัน from_attributes ไปอ่าน relationship
# LostItem.images ซึ่ง lazy load ไม่ได้ใน async session (MissingGreenlet)
STAFF_IMAGES_FIELD = Field(default_factory=list, validation_alias="staff_images")


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
    images: list[GuestImageResponse] = STAFF_IMAGES_FIELD


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
    images: list[GuestImageResponse] = STAFF_IMAGES_FIELD


class FoundItemDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_code: str
    report_type: LostType
    item_category: str
    item_name: str
    description: str | None
    private_verification_detail: str | None = None
    event_datetime: datetime
    location_detail: str | None
    custody_location: str | None
    reporter_email: str
    status: LostStatus
    created_at: datetime
    images: list[GuestImageResponse] = STAFF_IMAGES_FIELD


class LostItemDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_code: str
    report_type: LostType
    item_category: str
    item_name: str
    description: str | None
    private_verification_detail: str | None = None
    event_datetime: datetime
    location_detail: str | None
    reporter_email: str
    status: LostStatus
    created_at: datetime
    images: list[GuestImageResponse] = STAFF_IMAGES_FIELD


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
    email_sent: bool | None = None
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    found_item_id: UUID
    claimant_name: str
    claimant_email: str
    status: ClaimStatus
    return_status: ReturnStatus | None
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
    pickup_location: str | None = None
    email_sent: bool | None = None
    pickup_note: str | None = None
    private_verification_detail: str | None = None
    pickup_end_datetime: datetime | None = None
    pickup_datetime: datetime | None
    return_status: ReturnStatus | None
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


class UpdateReturnStatusRequest(BaseModel):
    return_status: ReturnStatus


class SchedulePickupRequest(BaseModel):
    pickup_datetime: datetime
    pickup_end_datetime: datetime | None = None
    pickup_location: str | None = Field(default=None, max_length=255)
    note: str | None = Field(default=None, max_length=2000)

    @field_validator("pickup_datetime")
    @classmethod
    def validate_pickup_hours(cls, value: datetime) -> datetime:
        zone = ZoneInfo("Asia/Bangkok")
        local = value.replace(tzinfo=zone) if value.tzinfo is None else value.astimezone(zone)
        if local.weekday() >= 5 or not time(8, 30) <= local.time() <= time(16, 30):
            raise ValueError("นัดรับได้เฉพาะจันทร์–ศุกร์ เวลา 08:30–16:30 น.")
        if local <= datetime.now(zone):
            raise ValueError("กรุณาเลือกวันและเวลานัดหมายที่ยังมาไม่ถึง")
        return value

    @model_validator(mode="after")
    def validate_range(self):
        if self.pickup_end_datetime is None:
            return self
        zone = ZoneInfo("Asia/Bangkok")
        def local(value):
            return value.replace(tzinfo=zone) if value.tzinfo is None else value.astimezone(zone)
        start, end = local(self.pickup_datetime), local(self.pickup_end_datetime)
        if start.date() != end.date() or end <= start or end.time() > time(16, 30):
            raise ValueError("เวลาสิ้นสุดต้องหลังเวลาเริ่มในวันเดียวกันและไม่เกิน 16:30")
        if any(value.minute not in (0, 30) or value.second or value.microsecond for value in (start, end)):
            raise ValueError("เลือกนาทีได้เฉพาะ 00 และ 30")
        return self


class PersonalLostFoundHistoryResponse(BaseModel):
    uid: str
    item_id: UUID
    item_code: str
    title: str
    report_type: LostType
    status: LostStatus
    note: str | None
    created_at: datetime
