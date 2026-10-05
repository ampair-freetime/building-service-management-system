"""Pydantic schemas for the self-service staff password reset API."""

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.security import validate_password_strength


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class PasswordResetRequestAccepted(BaseModel):
    """Same body for every outcome, so the response never reveals whether an account exists."""

    detail: str = (
        "If this email belongs to an active staff account, a reset link will be sent shortly."
    )


class PasswordResetTokenRequest(BaseModel):
    token: str = Field(min_length=20, max_length=512)


class PasswordResetConfirmRequest(PasswordResetTokenRequest):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_strength(cls, value: str) -> str:
        return validate_password_strength(value)


class PasswordResetValidationResponse(BaseModel):
    valid: bool = True
