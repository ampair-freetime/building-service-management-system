"""รูปแบบข้อมูลเข้าและออกของ API ล็อกอิน."""

from pydantic import BaseModel, Field

from app.schemas.staff import StaffResponse


class LoginRequest(BaseModel):
    """ข้อมูลที่ผู้ใช้ต้องส่งเพื่อล็อกอิน."""

    # identifier รับได้ทั้งอีเมลและรหัสพนักงาน
    identifier: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    """ข้อมูลที่ส่งกลับเมื่อล็อกอินสำเร็จ."""

    access_token: str
    token_type: str = "bearer"
    # ใช้ StaffResponse เพื่อรับประกันว่า password_hash ไม่หลุดออกจาก API
    staff: StaffResponse
