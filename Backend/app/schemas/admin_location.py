"""ข้อมูลเข้าและออกของ Admin location API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def normalize_floor(value: str | None) -> str | None:
    if isinstance(value, str):
        return " ".join(value.split()) or None
    return value


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


class AdminLocationBulkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locations: list[AdminLocationCreate] = Field(min_length=1, max_length=100)


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
