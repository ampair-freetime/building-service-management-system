from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import PriorityLevel, RequestStatus, RequestType


class GuestCleaningCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=255)
    priority: PriorityLevel = PriorityLevel.NORMAL
    reporter_email: EmailStr
    location_id: int = Field(gt=0)

    @field_validator("reporter_email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


# จากการแสกน QR code
class GuestLocationResponse(BaseModel):
    id: int
    floor: str | None
    area: str


class GuestCleaningCreateResponse(BaseModel):
    request_code: str
    status: RequestStatus
    request_type: RequestType
    location: str
    image_count: int
    created_at: datetime
    message: str


# สำหรับติดตามสถานะ
class GuestTrackingResponse(BaseModel):
    request_type: RequestType
    location: str
    status: RequestStatus
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
