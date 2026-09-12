from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ClaimStatus, LostStatus, LostType
from app.models.lost_found import LostClaim, LostItem


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

    item.status = LostStatus.APPROVED
    item.reviewed_by = staff_id

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
            LostClaim.status == ClaimStatus.PENDING,
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
            LostClaim.status == ClaimStatus.PENDING,
        )
    )

    claim = await session.scalar(statement)

    if claim is None:
        return None

    claim.status = ClaimStatus.APPROVED
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
            LostClaim.status == ClaimStatus.PENDING,
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