"""Pydantic schemas สำหรับตรวจข้อมูลบัญชีพนักงานก่อนเข้าและออก API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import AccountStatus, StaffRole


class StaffCreate(BaseModel):
    """ข้อมูลที่แอดมินต้องส่งเมื่อสร้างบัญชีพนักงาน."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=150)
    role: StaffRole

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        """เก็บอีเมลเป็นตัวพิมพ์เล็ก เพื่อป้องกันบัญชีซ้ำต่างกันแค่ตัวพิมพ์."""
        return str(value).strip().lower()

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        """รวมช่องว่างที่เกินมาในชื่อให้เหลือช่องเดียว ก่อนตรวจ min_length เพื่อกันชื่อว่าง."""
        if isinstance(value, str):
            return " ".join(value.split())
        return value


class StaffResponse(BaseModel):
    """ข้อมูลพนักงานที่อนุญาตให้ส่งออก API โดยไม่รวม password_hash."""

    # ทำให้ Pydantic อ่านข้อมูลจาก SQLAlchemy model ได้โดยตรง
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    role: StaffRole
    status: AccountStatus
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class StaffCreatedResponse(StaffResponse):
    """ผลการสร้างบัญชีและสถานะการส่งรหัสผ่านเริ่มต้น."""

    email_sent: bool
