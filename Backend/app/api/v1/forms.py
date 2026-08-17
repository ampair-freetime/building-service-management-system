"""Dependencies สำหรับประกอบ multipart form เป็น Pydantic models."""

from datetime import datetime
from typing import Annotated

from fastapi import Form, HTTPException, status
from pydantic import EmailStr, ValidationError

from app.schemas.lost_found_item import GuestFoundItemCreate, GuestLostItemCreate


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
