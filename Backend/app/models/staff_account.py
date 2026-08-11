"""Compatibility imports สำหรับโค้ดที่ยังใช้ชื่อ StaffAccount เดิม."""

from app.models.enums import AccountStatus, StaffRole
from app.models.staff import Staff

StaffAccount = Staff

__all__ = ["AccountStatus", "StaffAccount", "StaffRole"]
