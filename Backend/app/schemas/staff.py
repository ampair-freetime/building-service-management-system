"""Pydantic schemas สำหรับตรวจข้อมูลบัญชีพนักงานก่อนเข้าและออก API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import AccountStatus, StaffRole


class StaffCreate(BaseModel):
    """ข้อมูลที่แอดมินต้องส่งเมื่อสร้างบัญชีพนักงาน."""

    staff_code: str = Field(min_length=2, max_length=30, pattern=r"^[A-Za-z0-9_-]+$")
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8, max_length=128)
    role: StaffRole
    status: AccountStatus = AccountStatus.ACTIVE

    @field_validator("staff_code")
    @classmethod
    def normalize_staff_code(cls, value: str) -> str:
        """ตัดช่องว่างและเก็บรหัสพนักงานเป็นตัวพิมพ์ใหญ่ให้ค้นหาได้สม่ำเสมอ."""
        return value.strip().upper()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        """เก็บอีเมลเป็นตัวพิมพ์เล็ก เพื่อป้องกันบัญชีซ้ำต่างกันแค่ตัวพิมพ์."""
        return str(value).strip().lower()

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        """รวมช่องว่างที่เกินมาในชื่อให้เหลือช่องเดียว."""
        return " ".join(value.split())


class StaffResponse(BaseModel):
    """ข้อมูลพนักงานที่อนุญาตให้ส่งออก API โดยไม่รวม password_hash."""

    # ทำให้ Pydantic อ่านข้อมูลจาก SQLAlchemy model ได้โดยตรง
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    staff_code: str
    email: EmailStr
    full_name: str
    role: StaffRole
    status: AccountStatus
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
