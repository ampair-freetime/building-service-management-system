"""Business logic และคำสั่งฐานข้อมูลที่เกี่ยวกับบัญชีพนักงาน."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AccountStatus, RequestStatus, StaffRole
from app.models.invitation import StaffInvitation
from app.models.password_reset import StaffPasswordReset
from app.models.service_request import ServiceRequest
from app.models.staff import Staff
from app.models.staff_deletion_audit import StaffDeletionAudit
from app.schemas.staff import StaffUpdate

logger = logging.getLogger(__name__)


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


async def get_staff_for_update(session: AsyncSession, staff_id: UUID) -> Staff | None:
    """ใช้ lock บัญชีเดียวกันใน profile update, invitation และ deletion."""
    return await session.scalar(
        select(Staff)
        .where(Staff.id == staff_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


async def _invalidate_pending_links(session: AsyncSession, staff_id: UUID) -> None:
    """Invalidate unused invitation and password reset links; the caller commits."""
    now = datetime.now(UTC)
    for model in (StaffInvitation, StaffPasswordReset):
        await session.execute(
            update(model)
            .where(
                model.staff_id == staff_id,
                model.used_at.is_(None),
                model.invalidated_at.is_(None),
            )
            .values(invalidated_at=now)
        )


def _is_duplicate_staff_email(exc: IntegrityError) -> bool:
    original = exc.orig
    for error in (original, getattr(original, "__cause__", None)):
        if getattr(error, "constraint_name", None) == "ix_staff_email":
            return True
    return "UNIQUE constraint failed: staff.email" in str(original)


async def release_deleted_staff_email(session: AsyncSession, email: str) -> None:
    """Free a deleted identity's email; retain the old address in deletion audit."""
    account = await session.scalar(select(Staff).where(
        Staff.email == email, Staff.status == AccountStatus.DELETED
    ).with_for_update())
    if account is None:
        return
    audit = await session.scalar(select(StaffDeletionAudit.id).where(
        StaffDeletionAudit.deleted_staff_id == account.id
    ))
    if audit is None:
        # Legacy deleted rows may predate deletion auditing.
        session.add(StaffDeletionAudit(
            deleted_staff_id=account.id, deleted_email=account.email,
            deleted_full_name=account.full_name, deleted_role=account.role.value,
            deleted_by_staff_id=UUID(int=0),  # Unknown actor for legacy deletions.
        ))
    account.email = f"deleted-{account.id}@deleted.invalid"
    await _invalidate_pending_links(session, account.id)
    await session.flush()


async def update_staff_profile(
    session: AsyncSession, *, staff_id: UUID, payload: StaffUpdate, actor: Staff
) -> Staff:
    account = await get_staff_for_update(session, staff_id)
    if account is None or account.status == AccountStatus.DELETED:
        raise LookupError("Staff account not found")
    changes = {
        key: value
        for key, value in payload.model_dump(exclude_unset=True).items()
        if getattr(account, key) != value
    }
    if not changes:
        return account

    if "email" in changes:
        await release_deleted_staff_email(session, changes["email"])
        duplicate = await session.scalar(
            select(Staff.id).where(Staff.email == changes["email"], Staff.id != staff_id)
        )
        if duplicate is not None:
            raise DuplicateStaffError("Email already exists")

    try:
        if "email" in changes:
            # Keep activation tied to the address that completed setup.
            if account.is_activated and account.activated_email is None:
                account.activated_email = account.email
            # Links already sent to the old address must stop working.
            await _invalidate_pending_links(session, staff_id)
        for key, value in changes.items():
            setattr(account, key, value)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if _is_duplicate_staff_email(exc):
            raise DuplicateStaffError("Email already exists") from exc
        raise
    await session.refresh(account)
    logger.info("Staff profile updated; staff_id=%s actor_id=%s", staff_id, actor.id)
    return account


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
    account = await get_staff_for_update(session, staff_id)
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
    await _invalidate_pending_links(session, account.id)
    await session.commit()
