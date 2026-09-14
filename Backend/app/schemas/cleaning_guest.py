from dataclasses import Field
from datetime import datetime
from uuid import UUID


from pydantic import (
    BaseModel,
    field_validator,
    EmailStr,
    ConfigDict,
    model_validator,
    Field)

from app.models.enums import RequestStatus,PriorityLevel

class GuestCleaningCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True,extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(max_length=2000)
    category_id: int
    priority: PriorityLevel
    reporter_email: EmailStr
    location_id: int | None
    location_detail: str | None


    @field_validator("reporter_email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("location_detail")
    @classmethod
    def normalize_location_detail(cls, value:str | None) -> str | None:
            if value is None:
                return None
            return " ".join(value.split()) or None

    @model_validator(mode="after")
    def require_location(self) -> "GuestCleaningCreate":
        if not self.qr_token and not self.location_detail:
            raise ValueError("กรุณาแสกน QR code หรือ ระบุสถานที่")
        return self

#หมวดหมู่
class GuestCleaningCategoryResponse(BaseModel):
    id: int
    category_name: str

#จากการแสกน QR code
class GuestLocationResponse(BaseModel):
    building: str
    floor: str| None
    room: str | None
    area_type: str|None

#
class GuestCleaningCreateResponse(BaseModel):
    request_code: str
    status: RequestStatus
    category_name: str
    location: str
    image_count: int
    created_at: datetime
    message: str

# สำหรับติดตามสถานะ
class GuestTrackingResponse(BaseModel):
    request_code: str
    category_name: str
    location: str
    status: RequestStatus
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
