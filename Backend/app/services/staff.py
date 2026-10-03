"""Business logic และคำสั่งฐานข้อมูลที่เกี่ยวกับบัญชีพนักงาน."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AccountStatus, RequestStatus, StaffRole
from app.models.service_request import ServiceRequest
from app.models.staff import Staff
from app.models.staff_deletion_audit import StaffDeletionAudit


class DuplicateStaffError(Exception):
    """แจ้งว่าอีเมลซ้ำกับบัญชีที่มีอยู่."""


class StaffDeletionBlockedError(Exception):
    """Deletion violates a safety rule; assignments are included when relevant."""

    def __init__(self, message: str, assignments: list[ServiceRequest] | None = None):
        super().__init__(message)
        self.assignments = assignments or []


async def get_staff_by_id(session: AsyncSession, staff_id: UUID) -> Staff | None:
    """ค้นหาพนักงานด้วย UUID ซึ่งใช้เป็น subject ภายใน JWT."""
    return await session.get(Staff, staff_id)


async def get_staff_by_email(session: AsyncSession, email: str) -> Staff | None:
    """ค้นหาบัญชีด้วยอีเมล ซึ่งเก็บเป็นตัวพิมพ์เล็กเสมอ จึงแปลงข้อมูลที่รับมาก่อนเทียบ."""
    return await session.scalar(select(Staff).where(Staff.email == email.strip().lower()))


async def list_staff(session: AsyncSession) -> list[Staff]:
    """คืนเฉพาะบัญชีที่ยังไม่ถูกลบ เรียงตามลำดับที่สร้าง."""
    result = await session.scalars(
        select(Staff)
        .where(Staff.status != AccountStatus.DELETED)
        .order_by(Staff.created_at, Staff.email)
    )
    return list(result)


async def delete_staff_account(
    session: AsyncSession, *, staff_id: UUID, deleted_by: Staff
) -> None:
    """Soft-delete a staff account after checking work and administrator safeguards."""
    account = await session.get(Staff, staff_id)
    if account is None or account.status == AccountStatus.DELETED:
        raise LookupError("Staff account not found")
    if account.id == deleted_by.id:
        raise StaffDeletionBlockedError("You cannot delete your own account")

    if account.role == StaffRole.ADMIN and account.status == AccountStatus.ACTIVE:
        active_admin_count = await session.scalar(
            select(func.count())
            .select_from(Staff)
            .where(Staff.role == StaffRole.ADMIN, Staff.status == AccountStatus.ACTIVE)
        )
        if active_admin_count <= 1:
            raise StaffDeletionBlockedError("You cannot delete the last active administrator")

    unfinished_statuses = (
        RequestStatus.WAITING,
        RequestStatus.ASSIGNED,
        RequestStatus.RECEIVED,
        RequestStatus.IN_PROGRESS,
    )
    unfinished = list(
        await session.scalars(
            select(ServiceRequest)
            .where(
                ServiceRequest.assigned_staff_id == account.id,
                ServiceRequest.status.in_(unfinished_statuses),
            )
            .order_by(ServiceRequest.created_at)
        )
    )
    if unfinished:
        raise StaffDeletionBlockedError(
            "Reassign or unassign all unfinished work before deleting this account",
            unfinished,
        )

    session.add(
        StaffDeletionAudit(
            deleted_staff_id=account.id,
            deleted_email=account.email,
            deleted_full_name=account.full_name,
            deleted_role=account.role.value,
            deleted_by_staff_id=deleted_by.id,
        )
    )
    # Keeping the row preserves foreign-key references and historical staff identity.
    account.status = AccountStatus.DELETED
    await session.commit()
