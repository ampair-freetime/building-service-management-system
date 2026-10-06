import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.enums import ClaimStatus, LostStatus, LostType, ReturnStatus
from app.models.lost_found import (
    LostClaim,
    LostClaimReturnStatusHistory,
    LostItem,
    LostItemHistory,
)
from app.schemas.lost_found_item import GuestImageResponse
from app.services.lost_found import load_image_map
from app.services.object_storage import ObjectStorage, StorageOperationError

logger = logging.getLogger(__name__)

# คำขอรับของที่ยังไม่จบ ถ้าปิดรายการทั้งที่ยังมีคำขอพวกนี้ ผู้ยื่นจะค้างโดยไม่มีใครดูแล
ACTIVE_CLAIM_STATUSES = (
    ClaimStatus.PENDING,
    ClaimStatus.ADDITIONAL_INFO_REQUIRED,
    ClaimStatus.APPROVED,
    ClaimStatus.SCHEDULED,
)


class ActiveClaimExistsError(Exception):
    """ปิดรายการพบของไม่ได้เพราะยังมีคำขอรับของคืนที่ยังไม่จบ"""


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
                    url=storage.create_download_url(image.object_key),
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


async def approve_found_item(
    session: AsyncSession,
    item_id: UUID,
    staff_id: UUID,
) -> LostItem | None:
    """อนุมัติรายการของที่พบและบันทึกเจ้าหน้าที่ผู้ตรวจสอบ"""

    statement = (
        select(LostItem)
        .where(
            LostItem.id == item_id,
            LostItem.report_type == LostType.FOUND,
            LostItem.status == LostStatus.PENDING,
        )
    )

    item = await session.scalar(statement)

    if item is None:
        return None

    session.add(LostItemHistory(
        lost_item_id=item.id, staff_id=staff_id, old_status=item.status,
        new_status=LostStatus.APPROVED, note="เจ้าหน้าที่อนุมัติรายการ",
    ))
    item.status = LostStatus.APPROVED
    item.reviewed_by = staff_id

    await session.commit()
    await session.refresh(item)

    return item


async def approve_lost_item(
    session: AsyncSession,
    item_id: UUID,
    staff_id: UUID,
) -> LostItem | None:
    """อนุมัติประกาศของหายและบันทึกเจ้าหน้าที่ผู้ตรวจสอบ"""

    statement = (
        select(LostItem)
        .where(
            LostItem.id == item_id,
            LostItem.report_type == LostType.LOST,
            LostItem.status == LostStatus.PENDING,
        )
    )

    item = await session.scalar(statement)

    if item is None:
        return None

    session.add(LostItemHistory(
        lost_item_id=item.id, staff_id=staff_id, old_status=item.status,
        new_status=LostStatus.APPROVED, note="เจ้าหน้าที่อนุมัติรายการ",
    ))
    item.status = LostStatus.APPROVED
    item.reviewed_by = staff_id

    await session.commit()
    await session.refresh(item)

    return item  


async def reject_lost_item(
    session: AsyncSession,
    item_id: UUID,
    staff_id: UUID,
    reason: str,
) -> LostItem | None:
    """ปฏิเสธประกาศของหายและบันทึกเหตุผลการปฏิเสธ"""

    statement = (
        select(LostItem)
        .where(
            LostItem.id == item_id,
            LostItem.report_type == LostType.LOST,
            LostItem.status == LostStatus.PENDING,
        )
    )

    item = await session.scalar(statement)

    if item is None:
        return None

    session.add(LostItemHistory(
        lost_item_id=item.id, staff_id=staff_id, old_status=item.status,
        new_status=LostStatus.REJECTED, note=reason,
    ))
    item.status = LostStatus.REJECTED
    item.reviewed_by = staff_id
    item.review_note = reason

    await session.commit()
    await session.refresh(item)

    return item 


async def reject_found_item(
    session: AsyncSession,
    item_id: UUID,
    staff_id: UUID,
    reason: str,
) -> LostItem | None:
    """ปฏิเสธรายการของที่พบและบันทึกเหตุผลการปฏิเสธ"""

    statement = (
        select(LostItem)
        .where(
            LostItem.id == item_id,
            LostItem.report_type == LostType.FOUND,
            LostItem.status == LostStatus.PENDING,
        )
    )

    item = await session.scalar(statement)

    if item is None:
        return None

    session.add(LostItemHistory(
        lost_item_id=item.id, staff_id=staff_id, old_status=item.status,
        new_status=LostStatus.REJECTED, note=reason,
    ))
    item.status = LostStatus.REJECTED
    item.reviewed_by = staff_id
    item.review_note = reason

    await session.commit()
    await session.refresh(item)

    return item


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
        "found_item_id": claim.found_item_id,
        "claimant_name": claim.claimant_name,
        "claimant_email": claim.claimant_email,
        "proof_detail": claim.proof_detail,
        "status": claim.status,
        "pickup_datetime": claim.pickup_datetime,
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


async def approve_ownership_request(
    session: AsyncSession,
    claim_id: UUID,
    staff_id: UUID,
) -> LostClaim | None:
    """อนุมัติคำขอรับของคืนและบันทึกเจ้าหน้าที่ผู้ตรวจสอบ"""

    statement = (
        select(LostClaim)
        .where(
            LostClaim.id == claim_id,
            LostClaim.status.in_([ClaimStatus.PENDING, ClaimStatus.ADDITIONAL_INFO_REQUIRED]),
        )
    )

    claim = await session.scalar(statement)

    if claim is None:
        return None

    claim.status = ClaimStatus.APPROVED
    claim.return_status = ReturnStatus.PENDING
    claim.reviewed_by = staff_id

    await session.commit()
    await session.refresh(claim)

    return claim


async def request_additional_ownership_information(
    session: AsyncSession,
    claim_id: UUID,
    staff_id: UUID,
    message: str,
) -> LostClaim | None:
    """ขอข้อมูลเพิ่มเติมจากผู้ยื่นคำขอรับของคืน"""

    statement = (
        select(LostClaim)
        .where(
            LostClaim.id == claim_id,
            LostClaim.status.in_([ClaimStatus.PENDING, ClaimStatus.ADDITIONAL_INFO_REQUIRED]),
        )
    )

    claim = await session.scalar(statement)

    if claim is None:
        return None

    claim.status = ClaimStatus.ADDITIONAL_INFO_REQUIRED
    claim.reviewed_by = staff_id
    claim.review_note = message

    await session.commit()
    await session.refresh(claim)

    return claim


async def update_ownership_return_status(
    session: AsyncSession,
    claim_id: UUID,
    new_status: ReturnStatus,
    staff_id: UUID,
) -> LostClaim | None:
    """อัปเดตสถานะการคืนของและบันทึกประวัติ"""

    statement = (
        select(LostClaim)
        .where(
            LostClaim.id == claim_id,
            LostClaim.status.in_(
                [
                    ClaimStatus.APPROVED,
                    ClaimStatus.SCHEDULED,
                ]
            ),
        )
    )

    claim = await session.scalar(statement)

    if claim is None:
        return None

    old_status = claim.return_status

    claim.return_status = new_status

    history = LostClaimReturnStatusHistory(
        claim_id=claim.id,
        staff_id=staff_id,
        old_status=old_status,
        new_status=new_status,
    )

    session.add(history)

    if new_status == ReturnStatus.RETURNED:
        claim.status = ClaimStatus.COMPLETED
        # คืนของให้เจ้าของแล้ว จึงต้องเอาประกาศออกจากหน้า guest ใน commit เดียวกับ claim
        item = await session.get(LostItem, claim.found_item_id)
        if item is not None and item.status == LostStatus.APPROVED:
            item.status = LostStatus.CLAIMED
            session.add(
                LostItemHistory(
                    lost_item_id=item.id,
                    staff_id=staff_id,
                    old_status=LostStatus.APPROVED,
                    new_status=LostStatus.CLAIMED,
                    note="คืนของให้ผู้ยื่นคำขอแล้ว",
                )
            )

    await session.commit()
    await session.refresh(claim)

    return claim


async def schedule_pickup(
    session: AsyncSession,
    claim_id: UUID,
    pickup_datetime: datetime,
    pickup_location: str | None = None,
    note: str | None = None,
) -> LostClaim | None:
    """นัดวันและเวลารับของสำหรับ ownership request ที่ยืนยันแล้ว"""

    statement = (
        select(LostClaim)
        .where(
            LostClaim.id == claim_id,
            LostClaim.status.in_([ClaimStatus.APPROVED, ClaimStatus.SCHEDULED]),
        )
    )

    claim = await session.scalar(statement)

    if claim is None:
        return None

    claim.pickup_datetime = pickup_datetime
    claim.pickup_location = pickup_location
    claim.pickup_note = note
    claim.status = ClaimStatus.SCHEDULED

    await session.commit()
    await session.refresh(claim)

    return claim


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


async def reject_ownership_request(session: AsyncSession, claim_id: UUID, staff_id: UUID, reason: str):
    claim = await session.scalar(select(LostClaim).where(
        LostClaim.id == claim_id,
        LostClaim.status.in_([ClaimStatus.PENDING, ClaimStatus.ADDITIONAL_INFO_REQUIRED]),
    ).with_for_update())
    if claim is None:
        return None
    claim.status = ClaimStatus.REJECTED
    claim.reviewed_by = staff_id
    claim.review_note = reason
    await session.commit()
    await session.refresh(claim)
    return claim
