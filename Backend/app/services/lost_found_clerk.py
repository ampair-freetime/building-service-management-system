import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import LostStatus, LostType
from app.models.lost_found import (
    LostClaim,
    LostItem,
    LostItemHistory,
)
from app.schemas.lost_found_item import GuestImageResponse
from app.services.claim_lifecycle import ACTIVE_CLAIM_STATUSES, STATE_CONFLICT_MESSAGE
from app.services.image_urls import build_image_url
from app.services.lost_found import load_image_map
from app.services.object_storage import ObjectStorage, StorageOperationError

logger = logging.getLogger(__name__)

class ActiveClaimExistsError(Exception):
    """ปิดรายการพบของไม่ได้เพราะยังมีคำขอรับของคืนที่ยังไม่จบ"""


class LostFoundStateConflictError(Exception):
    """รายการมีอยู่จริง แต่สถานะเปลี่ยนไปแล้ว ส่วนใหญ่เพราะเจ้าหน้าที่อีกคนกดก่อน"""


async def load_staff_image_urls(
    session: AsyncSession,
    item_ids: list[UUID],
    storage: ObjectStorage | None,
) -> dict[UUID, list[GuestImageResponse]]:
    """สร้าง signed URL ของรูปทุกสถานะ เพื่อให้ staff เห็นรูปก่อนกดอนุมัติ

    ถ้า R2 ยังไม่ตั้งค่าหรือสร้าง URL ไม่ได้ จะคืน dict ว่าง ให้ staff ยังอ่านข้อมูลอื่นได้
    """
    if storage is None or not item_ids:
        return {}

    image_map = await load_image_map(session, item_ids)
    try:
        return {
            item_id: [
                GuestImageResponse(
                    id=image.id,
                    url=build_image_url(image.id),
                    content_type=image.content_type,
                    width=image.width,
                    height=image.height,
                )
                for image in images
            ]
            for item_id, images in image_map.items()
        }
    except StorageOperationError:
        logger.warning("Creating staff lost-found image URLs failed", exc_info=True)
        return {}


async def list_pending_found_items(session: AsyncSession) -> list[LostItem]:
    """คืนรายการของที่พบซึ่งกำลังรอเจ้าหน้าที่ธุรการตรวจสอบ"""

    statement = (
        select(LostItem)
        .where(
            LostItem.report_type == LostType.FOUND,
            LostItem.status == LostStatus.PENDING,
        )
        .order_by(LostItem.created_at.desc())
    )

    result = await session.scalars(statement)
    return list(result)


async def list_pending_lost_items(session: AsyncSession) -> list[LostItem]:
    """คืนรายการประกาศของหายซึ่งกำลังรอเจ้าหน้าที่ธุรการตรวจสอบ"""

    statement = (
        select(LostItem)
        .where(
            LostItem.report_type == LostType.LOST,
            LostItem.status == LostStatus.PENDING,
        )
        .order_by(LostItem.created_at.desc())
    )

    result = await session.scalars(statement)
    return list(result)


async def get_found_item_detail(
    session: AsyncSession,
    item_id: UUID,
) -> LostItem | None:
     """ ค้นหารายละเอียดของที่พบตาม id """

     statement = (
        select(LostItem)
        .where(
            LostItem.id == item_id,
            LostItem.report_type == LostType.FOUND,
        )
     )

     result = await session.scalar(statement)
     return result


async def get_lost_item_detail(
    session: AsyncSession,
    item_id: UUID,
) -> LostItem | None:
    """ค้นหารายละเอียดประกาศของหายตาม id"""

    statement = (
        select(LostItem)
        .where(
            LostItem.id == item_id,
            LostItem.report_type == LostType.LOST,
        )
    )

    result = await session.scalar(statement)
    return result


async def _lock_item_for_review(
    session: AsyncSession, item_id: UUID, report_type: LostType
) -> LostItem | None:
    """ล็อกรายการก่อนตรวจสถานะ ให้ clerk ที่กดพร้อมกันต้องรอกันทีละคน

    ไม่ใส่ status ใน WHERE เพื่อแยก "ไม่มีรายการนี้" (None → 404)
    ออกจาก "มีคนตัดสินไปแล้ว" (LostFoundStateConflictError → 409)
    """
    item = await session.scalar(
        select(LostItem)
        .where(LostItem.id == item_id, LostItem.report_type == report_type)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if item is None:
        return None
    if item.status != LostStatus.PENDING:
        raise LostFoundStateConflictError(STATE_CONFLICT_MESSAGE)
    return item


async def _review_item(
    session: AsyncSession,
    item_id: UUID,
    report_type: LostType,
    staff_id: UUID,
    new_status: LostStatus,
    reason: str | None = None,
) -> LostItem | None:
    item = await _lock_item_for_review(session, item_id, report_type)
    if item is None:
        return None

    session.add(LostItemHistory(
        lost_item_id=item.id, staff_id=staff_id, old_status=item.status,
        new_status=new_status,
        note=reason if reason is not None else "เจ้าหน้าที่อนุมัติรายการ",
    ))
    item.status = new_status
    item.reviewed_by = staff_id
    if reason is not None:
        item.review_note = reason

    await session.commit()
    await session.refresh(item)
    return item


async def approve_found_item(
    session: AsyncSession,
    item_id: UUID,
    staff_id: UUID,
) -> LostItem | None:
    """อนุมัติรายการของที่พบและบันทึกเจ้าหน้าที่ผู้ตรวจสอบ"""
    return await _review_item(session, item_id, LostType.FOUND, staff_id, LostStatus.APPROVED)


async def approve_lost_item(
    session: AsyncSession,
    item_id: UUID,
    staff_id: UUID,
) -> LostItem | None:
    """อนุมัติประกาศของหายและบันทึกเจ้าหน้าที่ผู้ตรวจสอบ"""
    return await _review_item(session, item_id, LostType.LOST, staff_id, LostStatus.APPROVED)


async def reject_lost_item(
    session: AsyncSession,
    item_id: UUID,
    staff_id: UUID,
    reason: str,
) -> LostItem | None:
    """ปฏิเสธประกาศของหายและบันทึกเหตุผลการปฏิเสธ"""
    return await _review_item(
        session, item_id, LostType.LOST, staff_id, LostStatus.REJECTED, reason
    )


async def reject_found_item(
    session: AsyncSession,
    item_id: UUID,
    staff_id: UUID,
    reason: str,
) -> LostItem | None:
    """ปฏิเสธรายการของที่พบและบันทึกเหตุผลการปฏิเสธ"""
    return await _review_item(
        session, item_id, LostType.FOUND, staff_id, LostStatus.REJECTED, reason
    )


async def list_pending_ownership_requests(
    session: AsyncSession,
) -> list[LostClaim]:
    """คืนรายการคำขอรับของคืนที่กำลังรอเจ้าหน้าที่ตรวจสอบ"""

    statement = (
        select(LostClaim)
        .where(
            LostClaim.status.in_(ACTIVE_CLAIM_STATUSES),
        )
        .order_by(LostClaim.created_at.desc())
    )

    result = await session.scalars(statement)
    return list(result)


async def get_ownership_request_detail(
    session: AsyncSession,
    claim_id: UUID,
) -> dict | None:
    """คืนรายละเอียดคำขอรับของคืนพร้อมข้อมูลของที่พบ"""

    statement = (
        select(LostClaim)
        .where(
            LostClaim.id == claim_id,
        )
    )

    claim = await session.scalar(statement)

    if claim is None:
        return None

    item = await session.get(LostItem, claim.found_item_id)

    if item is None:
        return None

    return {
        "id": claim.id,
        "claim_code": claim.claim_code,
        "found_item_id": claim.found_item_id,
        "claimant_name": claim.claimant_name,
        "claimant_email": claim.claimant_email,
        "proof_detail": claim.proof_detail,
        "status": claim.status,
        "pickup_datetime": claim.pickup_datetime,
        "pickup_end_datetime": claim.pickup_end_datetime,
        "pickup_location": claim.pickup_location,
        "pickup_note": claim.pickup_note,
        "private_verification_detail": item.private_verification_detail,
        "return_status": claim.return_status,
        "review_note": claim.review_note,
        "created_at": claim.created_at,
        "updated_at": claim.updated_at,
        "item_code": item.item_code,
        "item_name": item.item_name,
        "item_category": item.item_category,
        "description": item.description,
        "location_detail": item.location_detail,
        "custody_location": item.custody_location,
    }


async def close_lost_found_item(
    session: AsyncSession,
    item_id: UUID,
    report_type: LostType,
    staff_id: UUID,
) -> LostItem | None:
    """ปิดรายการที่เผยแพร่แล้ว เพื่อให้หายจากหน้า guest ที่แสดงเฉพาะสถานะ APPROVED"""

    statement = (
        select(LostItem)
        .where(
            LostItem.id == item_id,
            LostItem.report_type == report_type,
            LostItem.status == LostStatus.APPROVED,
        )
        .with_for_update()
    )

    item = await session.scalar(statement)

    if item is None:
        return None

    if report_type == LostType.FOUND:
        active_claim_id = await session.scalar(
            select(LostClaim.id)
            .where(
                LostClaim.found_item_id == item.id,
                LostClaim.status.in_(ACTIVE_CLAIM_STATUSES),
            )
            .limit(1)
        )
        if active_claim_id is not None:
            raise ActiveClaimExistsError(
                "มีคำขอรับของคืนที่ยังดำเนินการอยู่ กรุณาจัดการคำขอก่อนปิดรายการ"
            )

    item.status = LostStatus.CLOSED
    session.add(
        LostItemHistory(
            lost_item_id=item.id,
            staff_id=staff_id,
            old_status=LostStatus.APPROVED,
            new_status=LostStatus.CLOSED,
            note="เจ้าหน้าที่ปิดรายการ",
        )
    )

    await session.commit()
    await session.refresh(item)

    return item


async def list_personal_lost_found_history(session: AsyncSession, staff_id: UUID):
    records = (await session.execute(
        select(LostItemHistory, LostItem)
        .join(LostItem, LostItem.id == LostItemHistory.lost_item_id)
        .where(LostItemHistory.staff_id == staff_id)
        .order_by(LostItemHistory.created_at.desc())
    )).all()
    def row(item, status, note, created_at, uid):
        return dict(uid=uid, item_id=item.id, item_code=item.item_code,
                    title=item.item_name, report_type=item.report_type,
                    status=status, note=note, created_at=created_at)
    rows = [row(item, history.new_status, history.note, history.created_at,
                f"lost-history-{history.id}") for history, item in records]
    decision_ids = {item.id for history, item in records
                    if history.new_status in (LostStatus.APPROVED, LostStatus.REJECTED)}
    # Earlier approvals recorded only the reviewer on the item.
    legacy = await session.scalars(select(LostItem).where(
        LostItem.reviewed_by == staff_id,
        LostItem.status.in_([LostStatus.APPROVED, LostStatus.REJECTED, LostStatus.CLOSED]),
    ))
    rows.extend(row(item, LostStatus.REJECTED if item.status == LostStatus.REJECTED
                    else LostStatus.APPROVED, item.review_note,
                    item.updated_at, f"lost-review-{item.id}")
                for item in legacy if item.id not in decision_ids)
    return rows
