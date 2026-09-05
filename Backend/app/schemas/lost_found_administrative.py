from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from app.models.enums import LostType, LostStatus

class PendingFoundItemResponse (BaseModel) :
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
