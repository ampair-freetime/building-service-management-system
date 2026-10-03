"""ข้อมูลเข้าและออกของ Admin location API."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# คำนำหน้าที่ผู้ใช้มักพิมพ์ซ้ำกับ label "ชั้น" ที่ระบบเติมให้; เช็ก floor ก่อน fl (ยาวก่อนสั้น)
_FLOOR_PREFIX = re.compile(r"^(?:ชั้น|floor|fl(?:\.|(?=[\s\d])))\s*", re.IGNORECASE)


def normalize_floor(value: str | None) -> str | None:
    """แปลง floor ให้อยู่ในรูปแบบเดียว เช่น "ชั้น 01" → "1" และ "b1" → "B1"."""
    if not isinstance(value, str):
        return value
    text = " ".join(value.split())
    if not text:
        return None
    text = _FLOOR_PREFIX.sub("", text)
    if not text:
        raise ValueError("Floor must not be only a prefix")
    if text.isdecimal():
        # int() แปลงเลขไทยเป็นเลขอารบิกและตัด 0 นำหน้าให้ในขั้นเดียว
        text = str(int(text))
    return text.upper()


def normalize_area(value: str | None) -> str | None:
    if isinstance(value, str):
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("Area must not be blank")
        return normalized
    return value


class AdminLocationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    floor: str | None = Field(default=None, max_length=30)
    area: str = Field(min_length=1, max_length=100)

    @field_validator("floor", mode="before")
    @classmethod
    def clean_floor(cls, value: str | None) -> str | None:
        return normalize_floor(value)

    @field_validator("area", mode="before")
    @classmethod
    def clean_area(cls, value: str) -> str:
        return normalize_area(value)


class AdminLocationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    floor: str | None = Field(default=None, max_length=30)
    area: str | None = Field(default=None, max_length=100)

    @field_validator("floor", mode="before")
    @classmethod
    def clean_floor(cls, value: str | None) -> str | None:
        return normalize_floor(value)

    @field_validator("area", mode="before")
    @classmethod
    def clean_area(cls, value: str | None) -> str | None:
        return normalize_area(value)

    @model_validator(mode="after")
    def reject_null_area(self) -> "AdminLocationUpdate":
        if "area" in self.model_fields_set and self.area is None:
            raise ValueError("Area must not be null")
        return self


class AdminLocationStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_active: bool


class AdminLocationResponse(BaseModel):
    id: int
    floor: str | None
    area: str
    label: str
    is_active: bool
    qr_token: str | None
    qr_url: str | None
    created_at: datetime
    updated_at: datetime
