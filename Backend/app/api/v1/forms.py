"""Dependencies สำหรับประกอบ multipart form เป็น Pydantic models."""

from datetime import datetime
from typing import Annotated

from fastapi import Form, HTTPException, Request, UploadFile, status
from pydantic import EmailStr, ValidationError
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.core.config import settings
from app.models.enums import PriorityLevel
from app.schemas.cleaning_guest import GuestCleaningCreate
from app.schemas.lost_found_item import GuestFoundItemCreate, GuestLostItemCreate
from app.schemas.repair_guest import GuestRepairCreate


async def parse_guest_repair_form(
    request: Request,
    title: Annotated[str, Form(min_length=1, max_length=200)],
    reporter_email: Annotated[EmailStr, Form()],
    location_id: Annotated[int, Form(gt=0)],
    description: Annotated[str, Form(max_length=1000)] = "",
    priority: Annotated[PriorityLevel, Form()] = PriorityLevel.NORMAL,
) -> GuestRepairCreate:
    """ตรวจ multipart ของ repair ก่อนส่งข้อมูลให้ service."""
    form = await request.form()
    allowed_fields = set(GuestRepairCreate.model_fields) | {"image"}
    errors = [
        {
            "type": "extra_forbidden",
            "loc": ["body", field],
            "msg": "Extra inputs are not permitted",
        }
        for field in sorted(set(form) - allowed_fields)
    ]
    if errors:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=errors)
    # Scalar Form fields อาจเลือกค่าสุดท้ายเมื่อส่งซ้ำ จึงตรวจจำนวนเองเฉพาะช่องข้อความ
    duplicates = [
        {
            "type": "value_error",
            "loc": ["body", field],
            "msg": "Only one value is permitted",
        }
        for field in sorted(allowed_fields - {"image"})
        if len(form.getlist(field)) > 1
    ]
    if duplicates:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=duplicates)
    try:
        return _build_payload(
            GuestRepairCreate,
            title=title,
            description=description,
            priority=priority,
            reporter_email=reporter_email,
            location_id=location_id,
        )
    except HTTPException as exc:
        # ปรับเฉพาะ repair เพื่อคงรูปแบบ error ของ endpoint เดิม
        for error in exc.detail:
            error["loc"] = ["body", *error["loc"]]
        raise


async def parse_guest_image_uploads(request: Request) -> list[UploadFile]:
    """อ่านช่อง image ซ้ำจาก multipart แล้วคืนเฉพาะไฟล์จริงไม่เกินค่าที่กำหนด."""
    form = await request.form()
    uploads = [
        entry
        for entry in form.getlist("image")
        if isinstance(entry, StarletteUploadFile) and bool(entry.filename)
    ]
    if len(uploads) > settings.max_guest_images:
        for upload in uploads:
            await upload.close()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=[
                {
                    "type": "value_error",
                    "loc": ["body", "image"],
                    "msg": f"แนบรูปได้ไม่เกิน {settings.max_guest_images} รูป",
                }
            ],
        )
    return uploads


async def parse_guest_cleaning_form(
    request: Request,
    title: Annotated[str, Form(min_length=1, max_length=200)],
    reporter_email: Annotated[EmailStr, Form()],
    location_id: Annotated[int, Form(gt=0)],
    description: Annotated[str, Form(max_length=255)] = "",
    priority: Annotated[PriorityLevel, Form()] = PriorityLevel.NORMAL,
) -> GuestCleaningCreate:
    """แปลง multipart form เป็นคำร้อง Cleaning แล้วให้ schema ตรวจซ้ำ."""
    form = await request.form()
    allowed_fields = {"title", "description", "priority", "reporter_email", "location_id", "image"}
    unexpected_fields = sorted(set(form) - allowed_fields)
    if unexpected_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=[
                {
                    "type": "extra_forbidden",
                    "loc": ["body", field],
                    "msg": "Extra inputs are not permitted",
                }
                for field in unexpected_fields
            ],
        )
    return _build_payload(
        GuestCleaningCreate,
        title=title,
        description=description,
        priority=priority,
        reporter_email=reporter_email,
        location_id=location_id,
    )


def parse_guest_lost_item_form(
    item_category: Annotated[str, Form(min_length=1, max_length=100)],
    item_name: Annotated[str, Form(min_length=1, max_length=200)],
    event_datetime: Annotated[datetime, Form()],
    location_detail: Annotated[str, Form(min_length=1, max_length=255)],
    reporter_email: Annotated[EmailStr, Form()],
    description: Annotated[str | None, Form(max_length=2_000)] = None,
    location_id: Annotated[int | None, Form(ge=1)] = None,
) -> GuestLostItemCreate:
    """แปลงช่องของหายจาก multipart form แล้วใช้ schema ตรวจ business rules."""
    return _build_payload(
        GuestLostItemCreate,
        item_category=item_category,
        item_name=item_name,
        event_datetime=event_datetime,
        location_detail=location_detail,
        reporter_email=reporter_email,
        description=description,
        location_id=location_id,
    )


def parse_guest_found_item_form(
    item_category: Annotated[str, Form(min_length=1, max_length=100)],
    item_name: Annotated[str, Form(min_length=1, max_length=200)],
    event_datetime: Annotated[datetime, Form()],
    location_detail: Annotated[str, Form(min_length=1, max_length=255)],
    reporter_email: Annotated[EmailStr, Form()],
    custody_location: Annotated[str, Form(min_length=1, max_length=255)],
    private_verification_detail: Annotated[str, Form(min_length=1, max_length=2_000)],
    description: Annotated[str | None, Form(max_length=2_000)] = None,
    location_id: Annotated[int | None, Form(ge=1)] = None,
) -> GuestFoundItemCreate:
    """แปลงช่องพบของ โดยส่งรายละเอียดใช้ยืนยันเข้า private field."""
    return _build_payload(
        GuestFoundItemCreate,
        item_category=item_category,
        item_name=item_name,
        event_datetime=event_datetime,
        location_detail=location_detail,
        reporter_email=reporter_email,
        custody_location=custody_location,
        private_verification_detail=private_verification_detail,
        description=description,
        location_id=location_id,
    )


def _build_payload(model_type: type, **values: object):
    """เปลี่ยน Pydantic error เป็น HTTP 422 ที่ frontend อ่านได้."""
    try:
        return model_type.model_validate(values)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.errors(
                include_url=False,
                include_context=False,
                include_input=False,
            ),
        ) from exc
