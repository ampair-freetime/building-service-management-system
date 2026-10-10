"""Business logic ของการขอรับของคืน (claim) ฝั่ง guest."""

import logging
from datetime import datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ClaimStatus, LostStatus, LostType
from app.models.lost_found import LostClaim, LostItem
from app.schemas.lost_found_item import (
    GuestClaimCreatedResponse,
    GuestClaimStatusResponse,
    GuestItemClaim,
)

logger = logging.getLogger(__name__)


class ClaimItemNotFoundError(LookupError):
    """ไม่พบประกาศพบของที่เปิดให้ขอรับคืน."""


class ItemNotClaimableError(ValueError):
    """ประกาศมีอยู่จริงแต่สถานะไม่เปิดให้ขอรับคืนแล้ว."""


class DuplicateClaimError(ValueError):
    """อีเมลนี้มีคำขอที่ยังรอตรวจสอบกับประกาศนี้อยู่แล้ว."""


class ClaimNotFoundError(LookupError):
    """ไม่พบคำขอที่ตรงกับรหัสและอีเมลผู้ยื่น."""


class ClaimPersistenceError(RuntimeError):
    """ไม่สามารถบันทึกคำขอลงฐานข้อมูลได้."""


async def create_guest_claim(
    session: AsyncSession,
    *,
    item_code: str,
    payload: GuestItemClaim,
) -> GuestClaimCreatedResponse:
    """รับคำขอรับของคืนจาก guest แล้วบันทึกเป็นแถวใหม่สถานะ pending."""
    item = await _load_found_item(session, item_code=item_code, lock=True)

    # ของที่ยังไม่อนุมัติต้องตอบเหมือนไม่มีอยู่ ไม่งั้นจะกลายเป็นช่องเดาว่ามีของอะไรอยู่ในระบบบ้าง
    if item.status != LostStatus.APPROVED:
        if item.status == LostStatus.CLAIMED:
            raise ItemNotClaimableError("รายการนี้ถูกรับคืนไปแล้ว")
        raise ClaimItemNotFoundError("ไม่พบประกาศนี้")

    duplicate = await session.scalar(
        select(LostClaim.id).where(
            LostClaim.found_item_id == item.id,
            LostClaim.claimant_email == payload.claimant_email,
            LostClaim.status.in_([ClaimStatus.PENDING, ClaimStatus.ADDITIONAL_INFO_REQUIRED]),
        )
    )
    if duplicate is not None:
        raise DuplicateClaimError("คุณมีคำขอรับคืนของรายการนี้ที่รอตรวจสอบอยู่แล้ว")

    item_id, found_item_code = item.id, item.item_code
    for attempt in range(5):
        claim_id = uuid4()
        code = f"CLM-{datetime.now(ZoneInfo('Asia/Bangkok')):%Y%m%d}-{claim_id.hex[:8].upper()}"
        claim = LostClaim(
            id=claim_id,
            claim_code=code,
            found_item_id=item_id,
            claimant_name=payload.claimant_name,
            claimant_email=payload.claimant_email,
            proof_detail=payload.proof_detail,
            status=ClaimStatus.PENDING,
        )
        try:
            # A savepoint lets a short-code collision retry without losing the item lock.
            async with session.begin_nested():
                session.add(claim)
                await session.flush()
                await session.refresh(claim, ["created_at"])
            await session.commit()
            break
        except IntegrityError as exc:
            existing = await session.scalar(
                select(LostClaim.id).where(LostClaim.claim_code == code)
            )
            if existing is not None and attempt < 4:
                continue
            await session.rollback()
            if existing is not None:
                raise ClaimPersistenceError("ไม่สามารถสร้างรหัสคำขอได้ กรุณาลองใหม่") from exc
            raise DuplicateClaimError("คุณมีคำขอรับคืนของรายการนี้ที่รอตรวจสอบอยู่แล้ว") from exc
        except SQLAlchemyError as exc:
            await session.rollback()
            raise ClaimPersistenceError("ไม่สามารถบันทึกคำขอรับคืนได้") from exc

    return GuestClaimCreatedResponse(
        id=claim.id,
        claim_code=claim.claim_code,
        found_item_code=found_item_code,
        status=claim.status,
        created_at=claim.created_at,
        message="รับคำขอแล้ว กรุณารอเจ้าหน้าที่ตรวจสอบหลักฐาน",
    )


async def get_guest_claim_status(
    session: AsyncSession,
    *,
    item_code: str,
    claim_id: UUID,
    claimant_email: str,
) -> GuestClaimStatusResponse:
    """ให้ผู้ยื่นคำขอติดตามผลได้ โดยต้องรู้ทั้งรหัสคำขอและอีเมลที่ใช้ยื่น."""
    item = await _load_found_item(session, item_code=item_code)

    claim = await session.scalar(
        select(LostClaim).where(
            LostClaim.id == claim_id,
            LostClaim.found_item_id == item.id,
            LostClaim.claimant_email == claimant_email.strip().lower(),
        )
    )
    if claim is None:
        # ข้อความเดียวกันทั้งกรณีไม่มีคำขอและกรณีอีเมลไม่ตรง เพื่อกันการไล่เดาผู้ยื่น
        raise ClaimNotFoundError("ไม่พบคำขอนี้")

    return claim_status_response(claim, item)


def claim_status_response(claim, item):
    verified = claim.status in (ClaimStatus.APPROVED, ClaimStatus.SCHEDULED, ClaimStatus.COMPLETED)
    return GuestClaimStatusResponse(
        id=claim.id,
        claim_code=claim.claim_code,
        found_item_code=item.item_code,
        item_name=item.item_name,
        status=claim.status,
        return_status=claim.return_status,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
        staff_message=claim.staff_message
        if claim.status in (ClaimStatus.REJECTED, ClaimStatus.ADDITIONAL_INFO_REQUIRED)
        else None,
        custody_location=item.custody_location if verified else None,
        pickup_datetime=claim.pickup_datetime if verified else None,
        pickup_end_datetime=claim.pickup_end_datetime if verified else None,
        pickup_location=claim.pickup_location if verified else None,
        pickup_note=claim.pickup_note if verified else None,
    )


async def _load_claim_by_code(session, claim_code, claimant_email, *, lock=False):
    query = (
        select(LostClaim, LostItem)
        .join(LostItem, LostItem.id == LostClaim.found_item_id)
        .where(
            LostClaim.claim_code == claim_code.strip().upper(),
            LostClaim.claimant_email == claimant_email.strip().lower(),
            LostItem.deleted_at.is_(None),
        )
    )
    if lock:
        query = query.with_for_update(of=LostClaim).execution_options(populate_existing=True)
    row = (await session.execute(query)).first()
    if row is None:
        raise ClaimNotFoundError("ไม่พบคำขอนี้")
    return row


async def track_guest_claim(session, *, claim_code, claimant_email):
    claim, item = await _load_claim_by_code(session, claim_code, claimant_email)
    return claim_status_response(claim, item)


async def submit_claim_additional_info(session, *, claim_code, payload):
    claim, item = await _load_claim_by_code(
        session, claim_code, str(payload.claimant_email), lock=True
    )
    if claim.status != ClaimStatus.ADDITIONAL_INFO_REQUIRED:
        raise ItemNotClaimableError("คำขอนี้ไม่ได้อยู่ระหว่างรอหลักฐานเพิ่มเติม")
    claim.proof_detail += "\n\nหลักฐานเพิ่มเติมจากผู้ยื่น:\n" + payload.proof_detail
    claim.status = ClaimStatus.PENDING
    claim.staff_message = None
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateClaimError("มีคำขอที่รอตรวจสอบอยู่แล้ว") from exc
    await session.refresh(claim)
    return claim_status_response(claim, item)


async def _load_found_item(
    session: AsyncSession, *, item_code: str, lock: bool = False
) -> LostItem:
    """อ่านประกาศพบของตามรหัส โดยกรอง report_type ใน query ไม่ใช่เช็คทีหลัง."""
    query = select(LostItem).where(
        LostItem.item_code == item_code.strip().upper(),
        LostItem.report_type == LostType.FOUND,
        LostItem.deleted_at.is_(None),
    )
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    item = await session.scalar(query)
    if item is None:
        raise ClaimItemNotFoundError("ไม่พบประกาศนี้")
    return item
