"""Business logic ของการขอรับของคืน (claim) ฝั่ง guest."""

import logging
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
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
    item = await _load_found_item(session, item_code=item_code)

    # ของที่ยังไม่อนุมัติต้องตอบเหมือนไม่มีอยู่ ไม่งั้นจะกลายเป็นช่องเดาว่ามีของอะไรอยู่ในระบบบ้าง
    if item.status != LostStatus.APPROVED:
        if item.status == LostStatus.CLAIMED:
            raise ItemNotClaimableError("รายการนี้ถูกรับคืนไปแล้ว")
        raise ClaimItemNotFoundError("ไม่พบประกาศนี้")

    duplicate = await session.scalar(
        select(LostClaim.id).where(
            LostClaim.found_item_id == item.id,
            LostClaim.claimant_email == payload.claimant_email,
            LostClaim.status == ClaimStatus.PENDING,
        )
    )
    if duplicate is not None:
        raise DuplicateClaimError("คุณมีคำขอรับคืนของรายการนี้ที่รอตรวจสอบอยู่แล้ว")

    claim = LostClaim(
        id=uuid4(),
        found_item_id=item.id,
        claimant_name=payload.claimant_name,
        claimant_email=payload.claimant_email,
        proof_detail=payload.proof_detail,
        status=ClaimStatus.PENDING,
    )
    try:
        session.add(claim)
        await session.flush()
        # created_at มาจาก server_default จึงต้องอ่านกลับอย่างชัดเจน
        # การปล่อยให้ lazy load ตอน serialize จะพังด้วย MissingGreenlet ใน async context
        await session.refresh(claim, ["created_at"])
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise ClaimPersistenceError("ไม่สามารถบันทึกคำขอรับคืนได้") from exc

    return GuestClaimCreatedResponse(
        id=claim.id,
        found_item_code=item.item_code,
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

    return GuestClaimStatusResponse(
        id=claim.id,
        found_item_code=item.item_code,
        item_name=item.item_name,
        status=claim.status,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
        # เปิดเผยที่เก็บของต่อเมื่อเจ้าหน้าที่ตรวจหลักฐานผ่านแล้วเท่านั้น
        custody_location=(
            item.custody_location if claim.status == ClaimStatus.APPROVED else None
        ),
    )


async def _load_found_item(session: AsyncSession, *, item_code: str) -> LostItem:
    """อ่านประกาศพบของตามรหัส โดยกรอง report_type ใน query ไม่ใช่เช็คทีหลัง."""
    item = await session.scalar(
        select(LostItem).where(
            LostItem.item_code == item_code.strip().upper(),
            LostItem.report_type == LostType.FOUND,
            LostItem.deleted_at.is_(None),
        )
    )
    if item is None:
        raise ClaimItemNotFoundError("ไม่พบประกาศนี้")
    return item
