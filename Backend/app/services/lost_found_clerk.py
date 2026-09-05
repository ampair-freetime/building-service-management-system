from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import LostStatus, LostType
from app.models.lost_found import LostItem


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
