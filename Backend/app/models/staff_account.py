"""SQLAlchemy model สำหรับตารางบัญชีพนักงาน."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, Uuid, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StaffRole(str, Enum):
    """บทบาทที่ระบบรองรับ ใช้ทั้งในฐานข้อมูลและ API."""

    HOUSEKEEPER = "housekeeper"  # แม่บ้าน
    TECHNICIAN = "technician"  # ช่างเทคนิค
    COORDINATOR = "coordinator"  # ผู้ประสานงาน
    ADMIN = "admin"  # ผู้ดูแลระบบ


class StaffAccount(Base):
    """บัญชีสำหรับยืนยันตัวตนของพนักงานหนึ่งคน."""

    __tablename__ = "staff_accounts"

    # UUID ไม่เปิดเผยลำดับจำนวนผู้ใช้เหมือนเลข id ที่เพิ่มทีละหนึ่ง
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # รหัสพนักงานและอีเมลใช้ล็อกอินได้ จึงห้ามซ้ำและสร้าง index สำหรับค้นหา
    employee_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    # เก็บเฉพาะค่าแฮช Argon2 ห้ามเก็บหรือส่งรหัสผ่านจริงลงฐานข้อมูล
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[StaffRole] = mapped_column(
        SqlEnum(
            StaffRole,
            name="staff_role",
            values_callable=lambda roles: [role.value for role in roles],
        ),
        index=True,
    )
    # ปิดบัญชีได้โดยไม่ต้องลบประวัติพนักงาน
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    # ให้ฐานข้อมูลกำหนดเวลาเริ่มต้น เพื่อให้ทุกช่องทางที่เขียนข้อมูลใช้มาตรฐานเดียวกัน
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
