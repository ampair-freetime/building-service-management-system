"""Schemas สำหรับการคืนงานทำความสะอาด/งานซ่อมกลับเข้าคิวกลาง."""

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TaskReturnRequest(BaseModel):
    """เหตุผลเป็นข้อบังคับ เพื่อให้ Admin และประวัติงานรู้ว่าทำไมงานกลับเข้าคิว."""

    reason: str = Field(min_length=1, max_length=100)
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Return reason must not be empty")
        return value

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class TaskReturnResponse(BaseModel):
    """งานหลังคืน: สถานะกลับเป็น waiting และไม่มีผู้รับผิดชอบ."""

    id: UUID
    request_code: str
    title: str
    status: str
    assigned_staff: None = None
