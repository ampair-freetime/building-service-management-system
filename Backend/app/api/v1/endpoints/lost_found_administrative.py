from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.dependencies import AdministrativeStaff, DbSession
from app.schemas.lost_found_administrative import (
    FoundItemDetailResponse,
    PendingFoundItemResponse,
)
from app.services.lost_found_administrative import (
    approve_found_item,
    get_found_item_detail,
    list_pending_found_items,
)

router = APIRouter()


@router.get(
    "/pending-found-items",
    response_model=list[PendingFoundItemResponse],
)
async def get_pending_found_items(
    session: DbSession,
    _: AdministrativeStaff,
) -> list[PendingFoundItemResponse]:
    """คืนรายการของที่พบซึ่งกำลังรอเจ้าหน้าที่ธุรการตรวจสอบ"""
    return await list_pending_found_items(session)


@router.get(
    "/found-items/{item_id}",
    response_model=FoundItemDetailResponse,
)
async def get_found_item(
    item_id: UUID,
    session: DbSession,
    _: AdministrativeStaff,
) -> FoundItemDetailResponse:
    """คืนรายละเอียดของที่พบตาม ID"""
    item = await get_found_item_detail(session, item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Found item not found",
        )

    return item


@router.post(
    "/found-items/{item_id}/approve",
    response_model=FoundItemDetailResponse,
)
async def approve_found_item_report(
    item_id: UUID,
    session: DbSession,
    current_staff: AdministrativeStaff,
) -> FoundItemDetailResponse:
    """ อนุมัติรายการของที่พบโดยเจ้าหน้าที่ธุรการ"""

    item = await approve_found_item(
        session,
        item_id,
        current_staff.id,
    )
    
    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Pending found item not found",
        )

    return item
