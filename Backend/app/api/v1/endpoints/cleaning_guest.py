"""Guest API สำหรับสถานที่ สร้างคำร้อง Cleaning และติดตามสถานะ."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile, status
from pydantic import EmailStr

from app.api.dependencies import DbSession, OptionalObjectStorageClient
from app.api.v1.forms import parse_guest_cleaning_form
from app.schemas.cleaning_guest import (
    GuestCleaningCreate,
    GuestCleaningCreateResponse,
    GuestLocationResponse,
    GuestTrackingResponse,
)
from app.services.cleaning_guest import (
    LocationNotFoundError,
    RequestNotFoundError,
    RequestPersistenceError,
    create_guest_cleaning_request,
    get_guest_request_status,
    list_guest_locations,
    resolve_location_by_qr,
)
from app.services.images import InvalidImageError
from app.services.object_storage import StorageConfigurationError, StorageOperationError

router = APIRouter()


@router.get("/locations", response_model=list[GuestLocationResponse])
async def read_locations(session: DbSession) -> list[GuestLocationResponse]:
    """คืนสถานที่ที่เปิดใช้งานสำหรับ dropdown."""
    return await list_guest_locations(session)


@router.get("/locations/by-qr/{qr_token}", response_model=GuestLocationResponse)
async def read_location_by_qr(
    qr_token: Annotated[str, Path(min_length=1, max_length=255)],
    session: DbSession,
) -> GuestLocationResponse:
    """แปลง QR token เป็นสถานที่สำหรับเลือกไว้ล่วงหน้าในฟอร์ม."""
    try:
        return await resolve_location_by_qr(session, qr_token=qr_token)
    except LocationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "",
    response_model=GuestCleaningCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cleaning_request(
    payload: Annotated[GuestCleaningCreate, Depends(parse_guest_cleaning_form)],
    session: DbSession,
    storage: OptionalObjectStorageClient,
    image: Annotated[UploadFile | None, File()] = None,
) -> GuestCleaningCreateResponse:
    """สร้างคำร้อง Cleaning จาก multipart form และรับรูปได้ไม่เกินหนึ่งไฟล์."""
    if image is not None and image.filename and storage is None:
        await image.close()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ระบบจัดเก็บรูปภาพยังไม่ได้ตั้งค่า",
        )
    try:
        return await create_guest_cleaning_request(
            session,
            payload=payload,
            image_upload=image,
            storage=storage,
        )
    except (InvalidImageError, LocationNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except StorageConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ระบบจัดเก็บรูปภาพยังไม่ได้ตั้งค่า",
        ) from exc
    except StorageOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ไม่สามารถบันทึกรูปภาพได้ กรุณาลองใหม่",
        ) from exc
    except RequestPersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/{request_code}", response_model=GuestTrackingResponse)
async def read_cleaning_request(
    request_code: Annotated[str, Path(min_length=1, max_length=32)],
    session: DbSession,
    reporter_email: Annotated[EmailStr, Query()],
) -> GuestTrackingResponse:
    """ติดตามคำร้องด้วยรหัสและอีเมลของผู้แจ้ง."""
    try:
        return await get_guest_request_status(
            session,
            request_code=request_code,
            reporter_email=str(reporter_email),
        )
    except RequestNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
