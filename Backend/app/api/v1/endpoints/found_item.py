"""Guest API สำหรับสร้างและอ่านประกาศพบของ."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import EmailStr

from app.api.dependencies import DbSession, ObjectStorageClient
from app.api.v1.forms import parse_guest_found_item_form
from app.models.enums import LostType
from app.schemas.lost_found_item import (
    GuestClaimCreatedResponse,
    GuestClaimStatusResponse,
    GuestFoundItemCreate,
    GuestItemClaim,
    GuestItemCreatedResponse,
    GuestItemListResponse,
    GuestItemPublicResponse,
)
from app.services.images import InvalidImageError
from app.services.lost_found import (
    ItemPersistenceError,
    LocationNotFoundError,
    PublicItemNotFoundError,
    create_guest_item,
    get_public_item,
    list_public_items,
)
from app.services.lost_found_claim import (
    ClaimItemNotFoundError,
    ClaimNotFoundError,
    ClaimPersistenceError,
    DuplicateClaimError,
    ItemNotClaimableError,
    create_guest_claim,
    get_guest_claim_status,
)
from app.services.object_storage import StorageOperationError

router = APIRouter()


@router.post(
    "",
    response_model=GuestItemCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_found_item(
    payload: Annotated[GuestFoundItemCreate, Depends(parse_guest_found_item_form)],
    session: DbSession,
    storage: ObjectStorageClient,
    image: Annotated[UploadFile | None, File()] = None,
) -> GuestItemCreatedResponse:
    """รับรายงานพบของ โดยเก็บข้อมูลยืนยันไว้ private และส่งรูปไป R2."""
    try:
        return await create_guest_item(
            session,
            payload=payload,
            report_type=LostType.FOUND,
            image_upload=image,
            storage=storage,
        )
    except (InvalidImageError, LocationNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except StorageOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ไม่สามารถบันทึกรูปภาพได้ กรุณาลองใหม่",
        ) from exc
    except ItemPersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("", response_model=GuestItemListResponse)
async def read_found_items(
    session: DbSession,
    storage: ObjectStorageClient,
    limit: Annotated[int, Query(ge=1, le=200)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
    category: Annotated[str | None, Query(max_length=100)] = None,
    search: Annotated[str | None, Query(max_length=200)] = None,
) -> GuestItemListResponse:
    """แสดงเฉพาะประกาศพบของที่เจ้าหน้าที่อนุมัติแล้ว."""
    try:
        return await list_public_items(
            session,
            report_type=LostType.FOUND,
            storage=storage,
            limit=limit,
            offset=offset,
            category=category,
            search=search,
        )
    except StorageOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ไม่สามารถสร้าง URL รูปภาพได้",
        ) from exc


@router.get("/{item_code}", response_model=GuestItemPublicResponse)
async def read_found_item(
    item_code: str,
    session: DbSession,
    storage: ObjectStorageClient,
    reporter_email: Annotated[EmailStr | None, Query()] = None,
) -> GuestItemPublicResponse:
    """อ่านรายละเอียดประกาศพบของโดยไม่คืนข้อมูลยืนยันเจ้าของ.

    ผู้แจ้งส่ง reporter_email ของตัวเองมาด้วยเพื่อติดตามสถานะประกาศของตัวเองได้ทุกสถานะ
    """
    try:
        return await get_public_item(
            session,
            report_type=LostType.FOUND,
            item_code=item_code,
            storage=storage,
            reporter_email=reporter_email,
        )
    except PublicItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except StorageOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ไม่สามารถสร้าง URL รูปภาพได้",
        ) from exc


@router.post(
    "/{item_code}/claims",
    response_model=GuestClaimCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_found_item_claim(
    item_code: str,
    payload: GuestItemClaim,
    session: DbSession,
) -> GuestClaimCreatedResponse:
    """รับคำขอรับของคืนจาก guest โดยไม่คืนข้อมูลที่ใช้ยืนยันตัวเจ้าของ."""
    try:
        return await create_guest_claim(
            session,
            item_code=item_code,
            payload=payload,
        )
    except ClaimItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (ItemNotClaimableError, DuplicateClaimError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except ClaimPersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get(
    "/{item_code}/claims/{claim_id}",
    response_model=GuestClaimStatusResponse,
)
async def read_found_item_claim(
    item_code: str,
    claim_id: UUID,
    session: DbSession,
    claimant_email: Annotated[EmailStr, Query()],
) -> GuestClaimStatusResponse:
    """ให้ผู้ยื่นคำขอติดตามสถานะของตัวเอง โดยต้องยืนยันด้วยอีเมลที่ใช้ยื่น."""
    try:
        return await get_guest_claim_status(
            session,
            item_code=item_code,
            claim_id=claim_id,
            claimant_email=str(claimant_email),
        )
    except (ClaimItemNotFoundError, ClaimNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str("ไม่พบคำขอนี้"),
        ) from exc
