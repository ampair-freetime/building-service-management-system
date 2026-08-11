"""Enum ส่วนกลางที่ใช้ร่วมกันระหว่าง SQLAlchemy models."""

from enum import Enum


class StaffRole(str, Enum):
    TECHNICIAN = "technician"
    HOUSEKEEPER = "housekeeper"
    CLERK = "clerk"
    ADMIN = "admin"


class AccountStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class RequestType(str, Enum):
    REPAIR = "repair"
    CLEANING = "cleaning"


class RequestStatus(str, Enum):
    WAITING = "waiting"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PriorityLevel(str, Enum):
    NORMAL = "normal"
    URGENT = "urgent"


class ImageType(str, Enum):
    BEFORE = "before"
    DURING = "during"
    AFTER = "after"


class LostType(str, Enum):
    LOST = "lost"
    FOUND = "found"


class LostStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CLAIMED = "claimed"
    CLOSED = "closed"
    REJECTED = "rejected"


class ClaimStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class RequestAction(str, Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    STATUS_CHANGED = "status_changed"
    RETURNED = "returned"
    REASSIGNED = "reassigned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
