"""โหลด SQLAlchemy models ทั้งหมดให้ Base.metadata และ Alembic มองเห็น."""

from app.models.enums import (
    AccountStatus,
    ClaimStatus,
    ImageType,
    LostStatus,
    LostType,
    PriorityLevel,
    RequestAction,
    RequestStatus,
    RequestType,
    StaffRole,
)
from app.models.image import Image
from app.models.location import Location
from app.models.lost_found import LostClaim, LostItem, LostItemHistory
from app.models.notification import Notification
from app.models.service_request import RequestHistory, ServiceCategory, ServiceRequest
from app.models.staff import Staff

__all__ = [
    "AccountStatus",
    "ClaimStatus",
    "Image",
    "ImageType",
    "Location",
    "LostClaim",
    "LostItem",
    "LostItemHistory",
    "LostStatus",
    "LostType",
    "Notification",
    "PriorityLevel",
    "RequestAction",
    "RequestHistory",
    "RequestStatus",
    "RequestType",
    "ServiceCategory",
    "ServiceRequest",
    "Staff",
    "StaffRole",
]
