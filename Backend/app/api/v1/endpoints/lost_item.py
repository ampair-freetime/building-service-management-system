"""Guest API สำหรับสร้างและอ่านประกาศของหาย."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import EmailStr

from app.api.dependencies import DbSession, ObjectStorageClient
from app.api.v1.forms import parse_guest_lost_item_form
from app.models.enums import LostType
from app.schemas.lost_found_item import (
    GuestItemCreatedResponse,
    GuestItemListResponse,
    GuestItemPublicResponse,
    GuestLostItemCreate,
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
from app.services.object_storage import StorageOperationError

router = APIRouter()


@router.post(
    "",
    response_model=GuestItemCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_lost_item(
    payload: Annotated[GuestLostItemCreate, Depends(parse_guest_lost_item_form)],
    session: DbSession,
    storage: ObjectStorageClient,
    image: Annotated[UploadFile | None, File()] = None,
) -> GuestItemCreatedResponse:
    """รับรายงานของหายจาก guest และส่งรูปที่ตรวจแล้วไปเก็บใน R2."""
    try:
        return await create_guest_item(
            session,
            payload=payload,
            report_type=LostType.LOST,
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
async def read_lost_items(
    session: DbSession,
    storage: ObjectStorageClient,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    category: Annotated[str | None, Query(max_length=100)] = None,
    search: Annotated[str | None, Query(max_length=200)] = None,
) -> GuestItemListResponse:
    """แสดงเฉพาะประกาศของหายที่เจ้าหน้าที่อนุมัติแล้ว."""
    try:
        return await list_public_items(
            session,
            report_type=LostType.LOST,
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
async def read_lost_item(
    item_code: str,
    session: DbSession,
    storage: ObjectStorageClient,
    reporter_email: Annotated[EmailStr | None, Query()] = None,
) -> GuestItemPublicResponse:
    """อ่านรายละเอียดประกาศของหายหนึ่งรายการโดยไม่เผยข้อมูลส่วนตัว.

    ผู้แจ้งส่ง reporter_email ของตัวเองมาด้วยเพื่อติดตามสถานะประกาศของตัวเองได้ทุกสถานะ
    """
    try:
        return await get_public_item(
            session,
            report_type=LostType.LOST,
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
