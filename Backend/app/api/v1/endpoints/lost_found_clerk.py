from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import select

from app.api.dependencies import ClerkStaff, CurrentStaff, DbSession, OptionalObjectStorageClient
from app.models.enums import LostStatus, LostType
from app.models.lost_found import LostItem
from app.models.staff import Staff
from app.schemas.lost_found_clerk import (
    FoundItemDetailResponse,
    LostItemDetailResponse,
    OwnershipRequestDetailResponse,
    OwnershipRequestListResponse,
    PendingFoundItemResponse,
    PendingLostItemResponse,
    PersonalLostFoundHistoryResponse,
    RejectFoundItemRequest,
    RequestAdditionalInfoRequest,
    SchedulePickupRequest,
    UpdateReturnStatusRequest,
)
from app.services import claim_lifecycle
from app.services.claim_notifications import schedule_claim_notices, send_claim_notice
from app.services.lost_found_clerk import (
    ActiveClaimExistsError,
    LostFoundStateConflictError,
    approve_found_item,
    approve_lost_item,
    close_lost_found_item,
    get_found_item_detail,
    get_lost_item_detail,
    get_ownership_request_detail,
    list_pending_found_items,
    list_pending_lost_items,
    list_pending_ownership_requests,
    list_personal_lost_found_history,
    load_staff_image_urls,
    reject_found_item,
    reject_lost_item,
)

router = APIRouter()


@router.get("/items", response_model=list[FoundItemDetailResponse])
async def read_processed_items(
    session: DbSession, storage: OptionalObjectStorageClient, staff: CurrentStaff,
):
    if staff.role.value not in ("clerk", "admin"):
        raise HTTPException(status_code=403, detail="Clerk or admin access required")
    rows = (await session.execute(
        select(LostItem, Staff.full_name)
        .outerjoin(Staff, LostItem.reviewed_by == Staff.id)
        .where(
            LostItem.status.in_([LostStatus.APPROVED, LostStatus.CLAIMED]),
            LostItem.deleted_at.is_(None),
        )
        .order_by(LostItem.created_at.desc())
    )).all()
    items = [item for item, _ in rows]
    image_urls = await load_staff_image_urls(session, [item.id for item in items], storage)
    reviewer_names = {item.id: reviewer_name for item, reviewer_name in rows}
    return [FoundItemDetailResponse.model_validate(item).model_copy(
        update={
            "images": image_urls.get(item.id, []),
            "reviewer_name": reviewer_names.get(item.id),
        }
    ) for item in items]


@router.get("/my-history", response_model=list[PersonalLostFoundHistoryResponse])
async def read_personal_history(session: DbSession, staff: ClerkStaff):
    return await list_personal_lost_found_history(session, staff.id)


@router.get(
    "/pending-found-items",
    response_model=list[PendingFoundItemResponse],
)
async def get_pending_found_items(
    session: DbSession,
    storage: OptionalObjectStorageClient,
    _: ClerkStaff,
) -> list[PendingFoundItemResponse]:
    """คืนรายการของที่พบซึ่งกำลังรอเจ้าหน้าที่ธุรการตรวจสอบ"""
    items = await list_pending_found_items(session)
    image_urls = await load_staff_image_urls(session, [item.id for item in items], storage)
    return [
        PendingFoundItemResponse.model_validate(item).model_copy(
            update={"images": image_urls.get(item.id, [])}
        )
        for item in items
    ]


@router.get(
    "/pending-lost-items",
    response_model=list[PendingLostItemResponse],
)
async def get_pending_lost_items(
    session: DbSession,
    storage: OptionalObjectStorageClient,
    _: ClerkStaff,
) -> list[PendingLostItemResponse]:
    """คืนรายการประกาศของหายซึ่งกำลังรอเจ้าหน้าที่ธุรการตรวจสอบ"""
    items = await list_pending_lost_items(session)
    image_urls = await load_staff_image_urls(session, [item.id for item in items], storage)
    return [
        PendingLostItemResponse.model_validate(item).model_copy(
            update={"images": image_urls.get(item.id, [])}
        )
        for item in items
    ]


@router.get(
    "/found-items/{item_id}",
    response_model=FoundItemDetailResponse,
)
async def get_found_item(
    item_id: UUID,
    session: DbSession,
    storage: OptionalObjectStorageClient,
    _: ClerkStaff,
) -> FoundItemDetailResponse:
    """คืนรายละเอียดของที่พบตาม ID พร้อมรูปสำหรับตรวจสอบ"""
    item = await get_found_item_detail(session, item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Found item not found",
        )

    image_urls = await load_staff_image_urls(session, [item.id], storage)
    return FoundItemDetailResponse.model_validate(item).model_copy(
        update={"images": image_urls.get(item.id, [])}
    )


@router.get(
    "/lost-items/{item_id}",
    response_model=LostItemDetailResponse,
)
async def get_lost_item(
    item_id: UUID,
    session: DbSession,
    storage: OptionalObjectStorageClient,
    _: ClerkStaff,
) -> LostItemDetailResponse:
    """คืนรายละเอียดประกาศของหายตาม ID พร้อมรูปสำหรับตรวจสอบ"""

    item = await get_lost_item_detail(session, item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Lost item not found",
        )

    image_urls = await load_staff_image_urls(session, [item.id], storage)
    return LostItemDetailResponse.model_validate(item).model_copy(
        update={"images": image_urls.get(item.id, [])}
    )


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

    try:
        item = await approve_found_item(
            session,
            item_id,
            current_staff.id,
        )
    except LostFoundStateConflictError as exc:
        # เจ้าหน้าที่อีกคนดำเนินการไปก่อนแล้ว
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    
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

    try:
        item = await approve_lost_item(
            session,
            item_id,
            current_staff.id,
        )
    except LostFoundStateConflictError as exc:
        # เจ้าหน้าที่อีกคนดำเนินการไปก่อนแล้ว
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Pending lost item not found",
        )

    return item


@router.post(
    "/lost-items/{item_id}/reject",
    response_model=LostItemDetailResponse,
)
async def reject_lost_item_report(
    item_id: UUID,
    request: RejectFoundItemRequest,
    session: DbSession,
    current_staff: ClerkStaff,
) -> LostItemDetailResponse:
    """ปฏิเสธประกาศของหายโดยเจ้าหน้าที่ธุรการ"""

    try:
        item = await reject_lost_item(
            session,
            item_id,
            current_staff.id,
            request.reason,
        )
    except LostFoundStateConflictError as exc:
        # เจ้าหน้าที่อีกคนดำเนินการไปก่อนแล้ว
        raise HTTPException(status_code=409, detail=str(exc)) from exc

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

    try:
        item = await reject_found_item(
            session,
            item_id,
            current_staff.id,
            request.reason,
        )
    except LostFoundStateConflictError as exc:
        # เจ้าหน้าที่อีกคนดำเนินการไปก่อนแล้ว
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Pending found item not found",
        )

    return item


@router.post(
    "/found-items/{item_id}/close",
    response_model=FoundItemDetailResponse,
)
async def close_found_item_report(
    item_id: UUID,
    session: DbSession,
    current_staff: ClerkStaff,
) -> FoundItemDetailResponse:
    """ปิดรายการของที่พบซึ่งเผยแพร่แล้ว เพื่อเอาออกจากหน้า guest"""

    try:
        item = await close_lost_found_item(
            session,
            item_id,
            LostType.FOUND,
            current_staff.id,
        )
    except ActiveClaimExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Approved found item not found",
        )

    return item


@router.post(
    "/lost-items/{item_id}/close",
    response_model=LostItemDetailResponse,
)
async def close_lost_item_report(
    item_id: UUID,
    session: DbSession,
    current_staff: ClerkStaff,
) -> LostItemDetailResponse:
    """ปิดประกาศของหายที่เผยแพร่แล้ว เช่น เจ้าของได้ของคืนแล้ว"""

    item = await close_lost_found_item(
        session,
        item_id,
        LostType.LOST,
        current_staff.id,
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Approved lost item not found",
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
    """คืนรายการคำขอรับของคืนที่ยังอยู่ระหว่างดำเนินการ"""

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


# ---------------------------------------------------------------- คำขอรับของคืน
# กฎสถานะ ลำดับ lock และอีเมลอยู่ใน services/claim_lifecycle.py; ที่นี่แค่แปลงเป็น HTTP


@contextmanager
def _claim_http_errors() -> Iterator[None]:
    try:
        yield
    except claim_lifecycle.ClaimNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except claim_lifecycle.ClaimConflictError as exc:
        # เจ้าหน้าที่อีกคนดำเนินการไปก่อนแล้ว หรือสถานะไม่อนุญาตคำสั่งนี้
        raise HTTPException(status_code=409, detail=str(exc)) from exc


async def _send_and_report(outcome: claim_lifecycle.ClaimOutcome) -> bool:
    """รอส่งอีเมลเพื่อบอกเจ้าหน้าที่ว่าผู้ขอได้รับแจ้งหรือยัง (commit ไปแล้ว ไม่ถือ lock)."""
    results = [await send_claim_notice(notice) for notice in outcome.notices]
    return all(results)


@router.post(
    "/ownership-requests/{claim_id}/approve",
    response_model=OwnershipRequestListResponse,
)
async def approve_ownership_request_endpoint(
    claim_id: UUID,
    session: DbSession,
    current_staff: ClerkStaff,
    background_tasks: BackgroundTasks,
) -> OwnershipRequestListResponse:
    """อนุมัติคำขอรับของคืน; คำขออื่นของของชิ้นเดียวกันถูกปฏิเสธและแจ้งทางอีเมลเบื้องหลัง"""
    with _claim_http_errors():
        outcome = await claim_lifecycle.approve(session, claim_id, current_staff.id)
    schedule_claim_notices(background_tasks, outcome.notices)
    return outcome.claim


@router.post(
    "/ownership-requests/{claim_id}/request-additional-info",
    response_model=OwnershipRequestListResponse,
)
async def request_additional_ownership_info(
    claim_id: UUID,
    request: RequestAdditionalInfoRequest,
    session: DbSession,
    current_staff: ClerkStaff,
    background_tasks: BackgroundTasks,
) -> OwnershipRequestListResponse:
    """ขอข้อมูลเพิ่มเติม; ผู้ขอได้อีเมลพร้อมลิงก์ไปส่งหลักฐานเพิ่ม"""
    with _claim_http_errors():
        outcome = await claim_lifecycle.request_additional_info(
            session, claim_id, current_staff.id, request.message
        )
    schedule_claim_notices(background_tasks, outcome.notices)
    return outcome.claim


@router.patch(
    "/ownership-requests/{claim_id}/return-status",
    response_model=OwnershipRequestListResponse,
)
async def update_return_status(
    claim_id: UUID,
    request: UpdateReturnStatusRequest,
    session: DbSession,
    current_staff: ClerkStaff,
) -> OwnershipRequestListResponse:
    with _claim_http_errors():
        outcome = await claim_lifecycle.update_return_status(
            session, claim_id, request.return_status, current_staff.id
        )
    return outcome.claim


@router.post(
    "/ownership-requests/{claim_id}/schedule-pickup",
    response_model=OwnershipRequestDetailResponse,
)
async def schedule_ownership_pickup(
    claim_id: UUID,
    request: SchedulePickupRequest,
    session: DbSession,
    _: ClerkStaff,
) -> OwnershipRequestDetailResponse:
    with _claim_http_errors():
        outcome = await claim_lifecycle.schedule_pickup(
            session,
            claim_id,
            pickup_datetime=request.pickup_datetime,
            pickup_end_datetime=request.pickup_end_datetime,
            pickup_location=request.pickup_location,
            note=request.note,
        )
    detail = await get_ownership_request_detail(session, claim_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Ownership request not found")
    detail["email_sent"] = await _send_and_report(outcome)
    return detail


@router.post("/ownership-requests/{claim_id}/reject", response_model=OwnershipRequestListResponse)
async def reject_ownership_request_endpoint(
    claim_id: UUID, request: RejectFoundItemRequest, session: DbSession, staff: ClerkStaff,
) -> OwnershipRequestListResponse:
    with _claim_http_errors():
        outcome = await claim_lifecycle.reject(session, claim_id, staff.id, request.reason)
    email_sent = await _send_and_report(outcome)
    return OwnershipRequestListResponse.model_validate(outcome.claim).model_copy(
        update={"email_sent": email_sent}
    )


@router.post("/ownership-requests/{claim_id}/release", response_model=OwnershipRequestListResponse)
async def release_ownership_request_endpoint(
    claim_id: UUID, request: RejectFoundItemRequest, session: DbSession, staff: ClerkStaff,
) -> OwnershipRequestListResponse:
    """ยกเลิกคำขอที่อนุมัติแล้ว (เช่นผู้ขอไม่มารับ) แล้วเปิดประกาศพบของให้คนอื่นขอได้อีก"""
    with _claim_http_errors():
        outcome = await claim_lifecycle.release(session, claim_id, staff.id, request.reason)
    email_sent = await _send_and_report(outcome)
    return OwnershipRequestListResponse.model_validate(outcome.claim).model_copy(
        update={"email_sent": email_sent}
    )
