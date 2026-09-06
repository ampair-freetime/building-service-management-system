"""Schemas สำหรับ guest API ของประกาศของหายและของที่พบ."""

from datetime import UTC, datetime, timedelta
import string
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.models.enums import LostStatus, LostType

BANGKOK_TIMEZONE = ZoneInfo("Asia/Bangkok")


class GuestItemCreateBase(BaseModel):
    """ข้อมูลร่วมที่ guest ต้องกรอกทั้งประกาศของหายและของที่พบ."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    item_category: str = Field(min_length=1, max_length=100)
    item_name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2_000)
    event_datetime: datetime
    location_id: int | None = Field(default=None, ge=1)
    location_detail: str = Field(min_length=1, max_length=255)
    reporter_email: EmailStr

    @field_validator("item_category", "item_name", "location_detail")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        """รวมช่องว่างที่เกินมาเพื่อให้ค้นหาและแสดงผลสม่ำเสมอ."""
        return " ".join(value.split())

    @field_validator("description")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        """เปลี่ยนข้อความว่างเป็น None และเก็บบรรทัดที่ผู้ใช้ตั้งใจพิมพ์ไว้."""
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("reporter_email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("event_datetime")
    @classmethod
    def normalize_event_datetime(cls, value: datetime) -> datetime:
        """datetime-local จาก browser ถือเป็นเวลาไทย แล้วแปลงเป็น UTC ก่อนเก็บ."""
        if value.tzinfo is None:
            value = value.replace(tzinfo=BANGKOK_TIMEZONE)
        normalized = value.astimezone(UTC)
        if normalized > datetime.now(UTC) + timedelta(minutes=15):
            raise ValueError("วันและเวลาของเหตุการณ์ต้องไม่อยู่ในอนาคต")
        return normalized


class GuestLostItemCreate(GuestItemCreateBase):
    """ข้อมูลสร้างประกาศตามหาของ."""


class GuestFoundItemCreate(GuestItemCreateBase):
    """ข้อมูลสร้างประกาศพบของ โดยข้อมูลยืนยันจะไม่ถูกส่งออก public API."""

    custody_location: str = Field(min_length=1, max_length=255)
    private_verification_detail: str = Field(min_length=1, max_length=2_000)

    @field_validator("custody_location", "private_verification_detail")
    @classmethod
    def normalize_found_item_text(cls, value: str) -> str:
        return value.strip()


class GuestItemCreatedResponse(BaseModel):
    """ผลลัพธ์หลังรับรายงาน ซึ่งยังรอเจ้าหน้าที่ตรวจสอบ."""

    id: UUID
    item_code: str
    report_type: LostType
    status: LostStatus
    message: str


class GuestImageResponse(BaseModel):
    """รูป public พร้อม signed URL อายุสั้น โดยไม่เปิดเผย R2 object key."""

    id: UUID
    url: str
    content_type: str | None
    width: int | None
    height: int | None


class GuestItemPublicResponse(BaseModel):
    """ข้อมูลประกาศที่ผ่านการอนุมัติ โดยตัดอีเมลและรายละเอียดลับออก."""

    id: UUID
    item_code: str
    report_type: LostType
    item_category: str
    item_name: str
    description: str | None
    event_datetime: datetime
    location_id: int | None
    location_detail: str | None
    custody_location: str | None
    status: LostStatus
    created_at: datetime
    updated_at: datetime
    images: list[GuestImageResponse]


class GuestItemListResponse(BaseModel):
    """รายการประกาศพร้อมจำนวนทั้งหมดสำหรับทำ pagination."""

    items: list[GuestItemPublicResponse]
    total: int
    limit: int
    offset: int
