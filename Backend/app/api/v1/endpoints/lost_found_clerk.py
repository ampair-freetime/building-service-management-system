from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.dependencies import ClerkStaff, DbSession
from app.schemas.lost_found_clerk import (
    FoundItemDetailResponse,
    LostItemDetailResponse,
    OwnershipRequestDetailResponse,
    OwnershipRequestListResponse,
    PendingFoundItemResponse,
    PendingLostItemResponse,
    RejectFoundItemRequest,
    RequestAdditionalInfoRequest,
)
from app.services.lost_found_clerk import (
    approve_found_item,
    approve_lost_item,
    get_found_item_detail,
    get_lost_item_detail,
    get_ownership_request_detail,
    list_pending_found_items,
    list_pending_lost_items,
    list_pending_ownership_requests,
    reject_found_item,
    approve_ownership_request,
    request_additional_ownership_information,
)

router = APIRouter()

@router.get(
    "/pending-found-items",
    response_model=list[PendingFoundItemResponse],
)
async def get_pending_found_items(
    session: DbSession,
    _: ClerkStaff,
) -> list[PendingFoundItemResponse]:
    """คืนรายการของที่พบซึ่งกำลังรอเจ้าหน้าที่ธุรการตรวจสอบ"""
    return await list_pending_found_items(session)


@router.get(
    "/pending-lost-items",
    response_model=list[PendingLostItemResponse],
)
async def get_pending_lost_items(
    session: DbSession,
    _: ClerkStaff,
) -> list[PendingLostItemResponse]:
    """คืนรายการประกาศของหายซึ่งกำลังรอเจ้าหน้าที่ธุรการตรวจสอบ"""
    return await list_pending_lost_items(session)


@router.get(
    "/found-items/{item_id}",
    response_model=FoundItemDetailResponse,
)
async def get_found_item(
    item_id: UUID,
    session: DbSession,
    _: ClerkStaff,
) -> FoundItemDetailResponse:
    """คืนรายละเอียดของที่พบตาม ID"""
    item = await get_found_item_detail(session, item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Found item not found",
        )

    return item


@router.get(
    "/lost-items/{item_id}",
    response_model=LostItemDetailResponse,
)
async def get_lost_item(
    item_id: UUID,
    session: DbSession,
    _: ClerkStaff,
) -> LostItemDetailResponse:
    """คืนรายละเอียดประกาศของหายตาม ID"""

    item = await get_lost_item_detail(session, item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Lost item not found",
        )

    return item


@router.post(
    "/found-items/{item_id}/approve",
    response_model=FoundItemDetailResponse,
)
async def approve_found_item_report(
    item_id: UUID,
    session: DbSession,
    current_staff: ClerkStaff,
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


@router.post(
    "/lost-items/{item_id}/approve",
    response_model=LostItemDetailResponse,
)
async def approve_lost_item_report(
    item_id: UUID,
    session: DbSession,
    current_staff: ClerkStaff,
) -> LostItemDetailResponse:
    """อนุมัติประกาศของหายโดยเจ้าหน้าที่ธุรการ"""

    item = await approve_lost_item(
        session,
        item_id,
        current_staff.id,
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Pending lost item not found",
        )

    return item


@router.post(
    "/found-items/{item_id}/reject",
    response_model=FoundItemDetailResponse,
)
async def reject_found_item_report(
    item_id: UUID,
    request: RejectFoundItemRequest,
    session: DbSession,
    current_staff: ClerkStaff,
) -> FoundItemDetailResponse:
    """ปฏิเสธรายการของที่พบโดยเจ้าหน้าที่ธุรการ"""

    item = await reject_found_item(
        session,
        item_id,
        current_staff.id,
        request.reason,
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Pending found item not found",
        )

    return item


@router.get(
    "/ownership-requests",
    response_model=list[OwnershipRequestListResponse],
)
async def get_pending_ownership_requests(
    session: DbSession,
    _: ClerkStaff,
) -> list[OwnershipRequestListResponse]:
    """คืนรายการคำขอรับของคืนที่กำลังรอตรวจสอบ"""

    return await list_pending_ownership_requests(session)


@router.get(
    "/ownership-requests/{claim_id}",
    response_model=OwnershipRequestDetailResponse,
)
async def get_ownership_request(
    claim_id: UUID,
    session: DbSession,
    _: ClerkStaff,
) -> OwnershipRequestDetailResponse:
    """คืนรายละเอียดคำขอรับของคืน"""

    claim = await get_ownership_request_detail(
        session,
        claim_id,
    )

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Ownership request not found",
        )

    return claim


@router.post(
    "/ownership-requests/{claim_id}/approve",
    response_model=OwnershipRequestListResponse,
)
async def approve_ownership_request_endpoint(
    claim_id: UUID,
    session: DbSession,
    current_staff: ClerkStaff,
) -> OwnershipRequestListResponse:
    """อนุมัติคำขอรับของคืน"""

    claim = await approve_ownership_request(
        session,
        claim_id,
        current_staff.id,
    )

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Pending ownership request not found",
        )

    return claim


@router.post(
    "/ownership-requests/{claim_id}/request-additional-info",
    response_model=OwnershipRequestListResponse,
)
async def request_additional_ownership_info(
    claim_id: UUID,
    request: RequestAdditionalInfoRequest,
    session: DbSession,
    current_staff: ClerkStaff,
) -> OwnershipRequestListResponse:
    """ขอข้อมูลเพิ่มเติมสำหรับคำขอรับของคืน"""

    claim = await request_additional_ownership_information(
        session,
        claim_id,
        current_staff.id,
        request.message,
    )

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Pending ownership request not found",
        )

    return claim