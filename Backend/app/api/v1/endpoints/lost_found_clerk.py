from uuid import UUID
from zoneinfo import ZoneInfo
from app.services.invitation_email import send_email, EmailDeliveryError

from fastapi import APIRouter, HTTPException

from app.api.dependencies import ClerkStaff, DbSession, OptionalObjectStorageClient
from app.schemas.lost_found_clerk import (
    PersonalLostFoundHistoryResponse,
    FoundItemDetailResponse,
    LostItemDetailResponse,
    OwnershipRequestDetailResponse,
    OwnershipRequestListResponse,
    PendingFoundItemResponse,
    PendingLostItemResponse,
    RejectFoundItemRequest,
    RequestAdditionalInfoRequest,
    UpdateReturnStatusRequest,
    SchedulePickupRequest,
)
from app.models.enums import LostType
from app.services.lost_found_clerk import (
    list_personal_lost_found_history,
    reject_ownership_request,
    ActiveClaimExistsError,
    ItemAlreadyClaimedError,
    approve_found_item,
    approve_lost_item,
    close_lost_found_item,
    get_found_item_detail,
    get_lost_item_detail,
    get_ownership_request_detail,
    list_pending_found_items,
    list_pending_lost_items,
    list_pending_ownership_requests,
    load_staff_image_urls,
    reject_found_item,
    reject_lost_item,
    approve_ownership_request,
    request_additional_ownership_information,
    update_ownership_return_status,
    schedule_pickup,
)

router = APIRouter()


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

    item = await reject_lost_item(
        session,
        item_id,
        current_staff.id,
        request.reason,
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

    try:
        claim = await approve_ownership_request(
            session,
            claim_id,
            current_staff.id,
        )
    except ItemAlreadyClaimedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

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
    claim = await update_ownership_return_status(
        session,
        claim_id,
        request.return_status,
        current_staff.id,
    )

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Approved ownership request not found",
        )

    return claim


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
    claim = await schedule_pickup(
        session,
        claim_id,
        request.pickup_datetime,
        request.pickup_location,
        request.note,
        request.pickup_end_datetime,
    )

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Verified ownership request not found",
        )

    detail = await get_ownership_request_detail(session, claim_id)

    if detail is None:
        raise HTTPException(
            status_code=404,
            detail="Ownership request not found",
        )

    local = request.pickup_datetime
    zone = ZoneInfo("Asia/Bangkok")
    local = local.replace(tzinfo=zone) if local.tzinfo is None else local.astimezone(zone)
    end = request.pickup_end_datetime
    end = (end.replace(tzinfo=zone) if end.tzinfo is None else end.astimezone(zone)) if end else None
    time_label = local.strftime("%H:%M") + (f"–{end.strftime('%H:%M')}" if end else "")
    try:
        await send_email(
            recipient=detail["claimant_email"],
            subject=f"นัดรับคืน {detail['item_name']} · {local.strftime('%d/%m/%Y')}",
            body=(f"เรียน {detail['claimant_name']}\n\n"
                  "เจ้าหน้าที่ได้กำหนดนัดหมายรับคืนทรัพย์สินของท่าน โดยมีรายละเอียดดังนี้\n\n"
                  f"ทรัพย์สิน: {detail['item_name']}\n"
                  f"รหัสอ้างอิง: {detail['item_code']}\n"
                  f"วันที่นัดรับคืน: {local.strftime('%d/%m/%Y')}\n"
                  f"เวลารับคืน: {time_label} น.\n"
                  f"สถานที่รับคืน: {request.pickup_location or detail['custody_location'] or 'ติดต่อห้องธุรการ CSB'}\n"
                  f"หลักฐานที่ต้องนำมาเพื่อยืนยันการรับคืน: {request.note or 'ไม่ได้ระบุ กรุณาติดต่อธุรการก่อนเข้ารับของ'}\n\n"
                  "หากไม่สะดวกมารับคืนตามวันและเวลาที่กำหนด กรุณาติดต่อเจ้าหน้าที่ธุรการเพื่อประสานงานนัดหมายใหม่\n\n"
                  "ช่องทางติดต่อ\n"
                  "โทรศัพท์: 053-943433 หรือ 063-0807969\n"
                  "อีเมล: Compsci@cmu.ac.th\n"
                  "เวลาทำการ: วันจันทร์–ศุกร์ เวลา 08:30–16:30 น. (ยกเว้นวันหยุดนักขัตฤกษ์)"),
        )
        detail["email_sent"] = True
    except EmailDeliveryError:
        detail["email_sent"] = False
    return detail

@router.post("/ownership-requests/{claim_id}/reject", response_model=OwnershipRequestListResponse)
async def reject_ownership_request_endpoint(
    claim_id: UUID, request: RejectFoundItemRequest, session: DbSession, staff: ClerkStaff,
):
    claim = await reject_ownership_request(session, claim_id, staff.id, request.reason)
    if claim is None:
        raise HTTPException(status_code=409, detail="คำขอนี้ไม่อยู่ในสถานะที่ปฏิเสธได้")
    detail = await get_ownership_request_detail(session, claim_id)
    email_sent = False
    try:
        await send_email(
            recipient=claim.claimant_email,
            subject="ผลการตรวจสอบคำขอรับคืนสิ่งของ · อาคาร CSB",
            body=(f"เรียน {claim.claimant_name}\n\n"
                  f"คำขอรับคืน {detail['item_name']} ({detail['item_code']}) ไม่ผ่านการตรวจสอบ\n"
                  f"เหตุผล: {request.reason}\n\n"
                  "หากต้องการสอบถามเพิ่มเติม กรุณาติดต่อธุรการอาคาร CSB"),
        )
        email_sent = True
    except EmailDeliveryError:
        pass
    return OwnershipRequestListResponse.model_validate(claim).model_copy(
        update={"email_sent": email_sent}
    )
