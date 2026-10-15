from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ClaimStatus, LostStatus, ReturnStatus
from app.models.lost_found import (
    LostClaim,
    LostClaimReturnStatusHistory,
    LostItem,
    LostItemHistory,
)
from app.services.claim_notifications import ClaimNotice

# รอเจ้าหน้าที่ตัดสิน: guest ยื่นซ้ำไม่ได้ และเจ้าหน้าที่ approve/reject/ขอข้อมูลเพิ่มได้
OPEN_CLAIM_STATUSES = (ClaimStatus.PENDING, ClaimStatus.ADDITIONAL_INFO_REQUIRED)
# ยืนยันเจ้าของแล้ว รอนัด/รอมารับของ
VERIFIED_CLAIM_STATUSES = (ClaimStatus.APPROVED, ClaimStatus.SCHEDULED)
# ยังไม่จบ ถ้าปิดรายการพบของทั้งที่ยังมีคำขอพวกนี้ ผู้ยื่นจะค้างโดยไม่มีใครดูแล
ACTIVE_CLAIM_STATUSES = OPEN_CLAIM_STATUSES + VERIFIED_CLAIM_STATUSES

STATE_CONFLICT_MESSAGE = "รายการนี้มีเจ้าหน้าที่ดำเนินการไปแล้ว กรุณารีเฟรชข้อมูล"
AUTO_REJECT_NOTE = "รายการนี้ยืนยันเจ้าของแล้ว"


class ClaimAction(str, Enum):
    APPROVE = "approve"
    REQUEST_INFO = "request_additional_info"
    REJECT = "reject"
    SCHEDULE_PICKUP = "schedule_pickup"
    UPDATE_RETURN_STATUS = "update_return_status"
    # ผู้ขอไม่มารับของ / เจ้าหน้าที่อนุมัติผิดคน: ยกเลิกการอนุมัติและเปิดประกาศให้คนอื่นขอได้อีก
    RELEASE = "release"


ALLOWED_FROM: dict[ClaimAction, tuple[ClaimStatus, ...]] = {
    ClaimAction.APPROVE: OPEN_CLAIM_STATUSES,
    ClaimAction.REQUEST_INFO: OPEN_CLAIM_STATUSES,
    ClaimAction.REJECT: OPEN_CLAIM_STATUSES,
    ClaimAction.SCHEDULE_PICKUP: VERIFIED_CLAIM_STATUSES,
    ClaimAction.UPDATE_RETURN_STATUS: VERIFIED_CLAIM_STATUSES,
    ClaimAction.RELEASE: VERIFIED_CLAIM_STATUSES,
}


def allowed_actions(status: ClaimStatus) -> list[str]:
    """คำสั่งที่เจ้าหน้าที่ทำได้กับคำขอในสถานะนี้ (ส่งให้หน้าเว็บใช้ซ่อน/แสดงปุ่ม)."""
    return [action.value for action, statuses in ALLOWED_FROM.items() if status in statuses]


class ClaimNotFoundError(LookupError):
    """ไม่มีคำขอรับของคืน id นี้."""


class ClaimConflictError(RuntimeError):
    """คำขอมีอยู่ แต่สถานะตอนนี้ไม่อนุญาตคำสั่งนี้."""


@dataclass
class ClaimOutcome:
    """ผลของคำสั่ง: claim หลัง commit และอีเมลที่ควรส่ง (ยังไม่ได้ส่ง)."""

    claim: LostClaim
    notices: list[ClaimNotice] = field(default_factory=list)


# ---------------------------------------------------------------- คำสั่งของเจ้าหน้าที่


async def approve(session: AsyncSession, claim_id: UUID, staff_id: UUID) -> ClaimOutcome:
    """ยืนยันเจ้าของ เอาของออกจากหน้า guest และปฏิเสธคำขออื่นของ item เดียวกันใน commit เดียว.

    เพราะล็อก item ก่อน: ถ้าอนุมัติคำขอคนละคนของ item เดียวกันพร้อมกัน คนที่สองจะรอ lock
    แล้วเจอ item เป็น CLAIMED จึงไม่ได้เจ้าของสองคน
    """
    claim, item = await _lock(session, claim_id, ClaimAction.APPROVE)
    if item.status != LostStatus.APPROVED:
        await session.rollback()
        raise ClaimConflictError("รายการนี้ยืนยันเจ้าของไปแล้วหรือไม่ได้เผยแพร่อยู่")

    claim.status = ClaimStatus.APPROVED
    claim.return_status = ReturnStatus.PENDING
    claim.reviewed_by = staff_id
    _set_item_status(session, item, LostStatus.CLAIMED, staff_id, "ยืนยันเจ้าของแล้ว")

    # คำขอของคนอื่นที่ยังค้างจะไม่มีวันผ่านแล้ว ปิดให้เลยเพื่อไม่ให้ผู้ยื่นเห็นว่ารอตรวจสอบตลอดไป
    others = await session.scalars(
        select(LostClaim).where(
            LostClaim.found_item_id == item.id,
            LostClaim.id != claim.id,
            LostClaim.status.in_(OPEN_CLAIM_STATUSES),
        )
    )
    notices = []
    for other in others:
        _close(other, ClaimStatus.REJECTED, staff_id, AUTO_REJECT_NOTE)
        notices.append(_notice("rejected", other, item, message=AUTO_REJECT_NOTE))

    await session.commit()
    await session.refresh(claim)
    return ClaimOutcome(claim, notices)


async def request_additional_info(
    session: AsyncSession, claim_id: UUID, staff_id: UUID, message: str
) -> ClaimOutcome:
    """ขอหลักฐานเพิ่ม; ผู้ยื่นได้อีเมลพร้อมลิงก์ไปส่งข้อมูลเพิ่ม."""
    claim, item = await _lock(session, claim_id, ClaimAction.REQUEST_INFO)
    claim.status = ClaimStatus.ADDITIONAL_INFO_REQUIRED
    claim.reviewed_by = staff_id
    claim.review_note = message
    claim.staff_message = message
    notice = _notice("info_requested", claim, item, message=message)
    await session.commit()
    await session.refresh(claim)
    return ClaimOutcome(claim, [notice])


async def reject(
    session: AsyncSession, claim_id: UUID, staff_id: UUID, reason: str
) -> ClaimOutcome:
    """ปฏิเสธคำขอที่ยังไม่ตัดสิน; ประกาศพบของยังเปิดให้คนอื่นขอได้ตามเดิม."""
    claim, item = await _lock(session, claim_id, ClaimAction.REJECT)
    _close(claim, ClaimStatus.REJECTED, staff_id, reason)
    notice = _notice("rejected", claim, item, message=reason)
    await session.commit()
    await session.refresh(claim)
    return ClaimOutcome(claim, [notice])


async def release(
    session: AsyncSession, claim_id: UUID, staff_id: UUID, reason: str
) -> ClaimOutcome:
    """ยกเลิกคำขอที่อนุมัติแล้ว (เช่นผู้ขอไม่มารับ) แล้วเปิดประกาศให้คนอื่นขอได้อีก.

    ก่อนมีคำสั่งนี้ item ที่ CLAIMED แล้วไม่มีทางกลับไปเผยแพร่ได้เลย
    """
    claim, item = await _lock(session, claim_id, ClaimAction.RELEASE)
    _close(claim, ClaimStatus.REJECTED, staff_id, reason)
    if item.status == LostStatus.CLAIMED:
        _set_item_status(session, item, LostStatus.APPROVED, staff_id, f"ยกเลิกการรับคืน: {reason}")
    notice = _notice("released", claim, item, message=reason)
    await session.commit()
    await session.refresh(claim)
    return ClaimOutcome(claim, [notice])


async def schedule_pickup(
    session: AsyncSession,
    claim_id: UUID,
    *,
    pickup_datetime: datetime,
    pickup_end_datetime: datetime | None = None,
    pickup_location: str | None = None,
    note: str | None = None,
) -> ClaimOutcome:
    """นัดวันรับของ; นัดซ้ำได้ (เขียนทับเป็นนัดล่าสุด) และส่งอีเมลนัดทุกครั้ง."""
    claim, item = await _lock(session, claim_id, ClaimAction.SCHEDULE_PICKUP)
    claim.pickup_datetime = pickup_datetime
    claim.pickup_end_datetime = pickup_end_datetime
    claim.pickup_location = pickup_location
    claim.pickup_note = note
    claim.status = ClaimStatus.SCHEDULED
    notice = _notice(
        "pickup_scheduled",
        claim,
        item,
        message=note,
        pickup_start=pickup_datetime,
        pickup_end=pickup_end_datetime,
        pickup_location=pickup_location or item.custody_location,
    )
    await session.commit()
    await session.refresh(claim)
    return ClaimOutcome(claim, [notice])


async def update_return_status(
    session: AsyncSession, claim_id: UUID, new_status: ReturnStatus, staff_id: UUID
) -> ClaimOutcome:
    """อัปเดตสถานะการคืนของ; "คืนแล้ว" ปิดทั้งคำขอและประกาศใน commit เดียว."""
    claim, item = await _lock(session, claim_id, ClaimAction.UPDATE_RETURN_STATUS)
    if claim.return_status == new_status:
        # กดซ้ำด้วยค่าเดิม (หรือสองคนกดพร้อมกัน): ไม่มีอะไรเปลี่ยน จึงไม่เพิ่ม history
        await session.rollback()
        return ClaimOutcome(await _reload(session, claim_id))

    session.add(
        LostClaimReturnStatusHistory(
            claim_id=claim.id,
            staff_id=staff_id,
            old_status=claim.return_status,
            new_status=new_status,
        )
    )
    claim.return_status = new_status
    if new_status == ReturnStatus.RETURNED:
        claim.status = ClaimStatus.COMPLETED
        # คืนของให้เจ้าของแล้ว จึงต้องเอาประกาศออกจากหน้า guest ใน commit เดียวกับ claim
        if item.status in (LostStatus.APPROVED, LostStatus.CLAIMED):
            _set_item_status(
                session, item, LostStatus.CLOSED, staff_id, "คืนของให้ผู้ยื่นคำขอแล้ว"
            )
    await session.commit()
    await session.refresh(claim)
    return ClaimOutcome(claim)


# ---------------------------------------------------------------- ตัวช่วยภายใน


async def _lock(
    session: AsyncSession, claim_id: UUID, action: ClaimAction
) -> tuple[LostClaim, LostItem]:
    """ล็อก item ก่อน claim (ลำดับเดียวกันทุกคำสั่ง) แล้วตรวจว่าคำสั่งทำได้จากสถานะปัจจุบัน."""
    found_item_id = await session.scalar(
        select(LostClaim.found_item_id).where(LostClaim.id == claim_id)
    )
    if found_item_id is None:
        raise ClaimNotFoundError("Ownership request not found")
    item = await session.scalar(
        select(LostItem)
        .where(LostItem.id == found_item_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    claim = await session.scalar(
        select(LostClaim)
        .where(LostClaim.id == claim_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if claim is None or item is None:
        await session.rollback()
        raise ClaimNotFoundError("Ownership request not found")
    if claim.status not in ALLOWED_FROM[action]:
        await session.rollback()
        raise ClaimConflictError(STATE_CONFLICT_MESSAGE)
    return claim, item


async def _reload(session: AsyncSession, claim_id: UUID) -> LostClaim:
    claim = await session.get(LostClaim, claim_id, populate_existing=True)
    if claim is None:
        raise ClaimNotFoundError("Ownership request not found")
    return claim


def _close(claim: LostClaim, status: ClaimStatus, staff_id: UUID, reason: str) -> None:
    claim.status = status
    claim.reviewed_by = staff_id
    claim.review_note = reason
    claim.staff_message = reason


def _set_item_status(
    session: AsyncSession, item: LostItem, new_status: LostStatus, staff_id: UUID, note: str
) -> None:
    session.add(
        LostItemHistory(
            lost_item_id=item.id,
            staff_id=staff_id,
            old_status=item.status,
            new_status=new_status,
            note=note,
        )
    )
    item.status = new_status


def _notice(kind, claim: LostClaim, item: LostItem, **details) -> ClaimNotice:
    return ClaimNotice(
        kind=kind,
        recipient=claim.claimant_email,
        claimant_name=claim.claimant_name,
        claim_code=claim.claim_code,
        item_name=item.item_name,
        **details,
    )
