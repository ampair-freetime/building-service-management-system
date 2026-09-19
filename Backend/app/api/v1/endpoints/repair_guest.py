"""Guest API สำหรับสถานที่ สร้างคำร้อง Repair และติดตามสถานะ."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile, status
from pydantic import EmailStr

from app.api.dependencies import DbSession, OptionalObjectStorageClient
from app.api.v1.forms import parse_guest_repair_form
from app.schemas.repair_guest import (
    GuestRepairCreate,
    GuestRepairCreateResponse,
    GuestRepairLocationResponse,
    GuestRepairTrackingResponse,
)
from app.services.images import InvalidImageError
from app.services.object_storage import StorageConfigurationError, StorageOperationError
from app.services.repair_guest import (
    RepairLocationNotFoundError,
    RepairRequestNotFoundError,
    RepairRequestPersistenceError,
    create_guest_repair_request,
    get_guest_repair_status,
    list_guest_repair_locations,
    resolve_guest_repair_location_by_qr,
)

router = APIRouter()


@router.get("/locations", response_model=list[GuestRepairLocationResponse])
async def read_repair_locations(session: DbSession) -> list[GuestRepairLocationResponse]:
    """คืนสถานที่ที่เปิดใช้งานสำหรับ dropdown."""
    return await list_guest_repair_locations(session)


@router.get("/locations/by-qr/{qr_token}", response_model=GuestRepairLocationResponse)
async def read_repair_location_by_qr(
    qr_token: Annotated[str, Path(min_length=1, max_length=255)],
    session: DbSession,
) -> GuestRepairLocationResponse:
    """แปลง QR token เป็นสถานที่สำหรับเลือกไว้ล่วงหน้าในฟอร์ม."""
    try:
        return await resolve_guest_repair_location_by_qr(session, qr_token=qr_token)
    except RepairLocationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "",
    response_model=GuestRepairCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_repair_request(
    payload: Annotated[GuestRepairCreate, Depends(parse_guest_repair_form)],
    session: DbSession,
    storage: OptionalObjectStorageClient,
    image: Annotated[UploadFile | None, File()] = None,
) -> GuestRepairCreateResponse:
    """สร้างคำร้อง Repair จาก multipart form และรับรูปได้ไม่เกินหนึ่งไฟล์."""
    if image is not None and image.filename and storage is None:
        await image.close()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ระบบจัดเก็บรูปภาพยังไม่ได้ตั้งค่า",
        )
    try:
        return await create_guest_repair_request(
            session,
            payload=payload,
            image_upload=image,
            storage=storage,
        )
    except (InvalidImageError, RepairLocationNotFoundError) as exc:
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
    except RepairRequestPersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/{request_code}", response_model=GuestRepairTrackingResponse)
async def read_repair_request(
    request_code: Annotated[str, Path(min_length=1, max_length=32)],
    session: DbSession,
    reporter_email: Annotated[EmailStr, Query()],
) -> GuestRepairTrackingResponse:
    """ติดตามคำร้องด้วยรหัสและอีเมลของผู้แจ้ง."""
    try:
        return await get_guest_repair_status(
            session,
            request_code=request_code,
            reporter_email=str(reporter_email),
        )
    except RepairRequestNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
