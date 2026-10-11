"""ค่าตั้งต้นของ backend ซึ่งสามารถแทนที่ได้ด้วย environment variables."""

import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


def _environment_files() -> tuple[Path, ...] | Path | None:
    """Resolve dotenv paths independently of the process working directory."""
    override = os.getenv("BSMS_ENV_FILE")
    if override is not None:
        return Path(override).expanduser().resolve() if override else None
    return (BACKEND_DIR.parent / ".env", BACKEND_DIR / ".env")


class Settings(BaseSettings):
    """รวม configuration ของแอป ฐานข้อมูล CORS และ JWT ไว้จุดเดียว."""

    app_name: str = "Building Service Management System"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: list[str] = ["http://localhost:5173"]

    # URL สำหรับ SQLAlchemy async engine
    database_url: str = (
        "postgresql+asyncpg://building_service:building_service@localhost:5432/building_service"
    )

    # production ต้องกำหนด JWT_SECRET_KEY ใหม่ผ่าน environment variable
    jwt_secret_key: str = "development-only-change-this-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # Invitation links point to the frontend password-setup page. SMTP credentials
    # stay on the server and are intentionally never returned by an API.
    staff_activation_url: str = ""
    invitation_token_expire_hours: int = 24
    # Self-service password reset. Links are short-lived and requests are throttled
    # per account (cooldown) and per client IP (sliding window, single worker).
    staff_password_reset_url: str = ""
    password_reset_token_expire_minutes: int = Field(default=30, ge=5, le=1440)
    password_reset_cooldown_seconds: int = Field(default=60, ge=0, le=3600)
    password_reset_ip_limit: int = Field(default=10, ge=1, le=1000)
    password_reset_ip_window_seconds: int = Field(default=900, ge=1, le=86400)
    # ไม่ตั้ง SMTP_HOST = สร้างบัญชีได้ แต่ตอบ email_sent=false
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_starttls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout_seconds: float = Field(default=10, gt=0, le=120)
    mail_from: str = "Building Care <no-reply@example.com>"
    public_base_url: str = "http://localhost:5173"

    # Cloudflare R2 ใช้ S3-compatible API โดย credentials ต้องอยู่ฝั่ง backend เท่านั้น
    r2_account_id: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket_name: str | None = None
    r2_presigned_url_expire_seconds: int = Field(default=28800, ge=1, le=604800)
    # Stable image links (/api/v1/images/{id}?sig=...) are signed with this key, kept
    # separate from jwt_secret_key so rotating one never logs everyone out or breaks images.
    image_url_secret: str = "development-only-change-this-image-secret"
    # Each redirect creates a fresh R2 link that only needs to survive until the browser
    # starts downloading, so it can be short.
    image_redirect_url_expire_seconds: int = Field(default=300, ge=60, le=3600)
    r2_connect_timeout_seconds: float = Field(default=5, gt=0, le=120)
    r2_read_timeout_seconds: float = Field(default=15, gt=0, le=120)
    r2_total_max_attempts: int = Field(default=2, ge=1, le=5)

    # จำกัดทั้งขนาดไฟล์และจำนวน pixel เพื่อลดความเสี่ยงจากไฟล์ภาพผิดปกติ
    max_image_upload_bytes: int = Field(default=25 * 1024 * 1024, gt=0)
    max_guest_images: int = Field(default=5, ge=1, le=5)
    max_image_pixels: int = Field(default=50_000_000, gt=0)
    # รูปที่เก็บจริงใน R2: ย่อด้านยาวและบีบอัดให้เล็ก แยกจากขีดจำกัดของไฟล์ที่อัปโหลด
    image_max_dimension: int = Field(default=2048, ge=256, le=16383)
    image_webp_quality: int = Field(default=78, ge=1, le=100)
    max_image_output_bytes: int = Field(default=1 * 1024 * 1024, gt=0)
    max_image_processing_concurrency: int = Field(default=1, ge=1, le=16)

    # guest ไม่ได้เลือกจุดฝากเอง ทุกรายการพบของต้องนำไปฝากที่จุดเดียวกันตามที่หน้าเว็บแจ้งไว้
    default_custody_location: str = Field(default="ห้องธุรการ ชั้น 1", min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_deployment_settings(self) -> "Settings":
        if not self.staff_activation_url:
            self.staff_activation_url = f"{self.public_base_url.rstrip('/')}/staff/setup-password"
        if not self.staff_password_reset_url:
            self.staff_password_reset_url = (
                f"{self.public_base_url.rstrip('/')}/staff/reset-password"
            )
        if self.smtp_use_ssl and self.smtp_use_starttls:
            raise ValueError("Use either SMTP_USE_SSL or SMTP_USE_STARTTLS, not both")
        if bool(self.smtp_username) != bool(self.smtp_password):
            raise ValueError("SMTP_USERNAME and SMTP_PASSWORD must be configured together")
        if self.environment == "production":
            if (
                self.jwt_secret_key == "development-only-change-this-secret"
                or len(self.jwt_secret_key) < 32
            ):
                raise ValueError("Production requires a JWT_SECRET_KEY of at least 32 characters")
            if (
                self.image_url_secret == "development-only-change-this-image-secret"
                or len(self.image_url_secret) < 32
            ):
                raise ValueError("Production requires an IMAGE_URL_SECRET of at least 32 characters")
            for value in (
                self.public_base_url,
                self.staff_activation_url,
                self.staff_password_reset_url,
                *self.backend_cors_origins,
            ):
                parsed = urlsplit(value)
                if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                    raise ValueError("Production frontend URLs must be absolute HTTP(S) URLs")
                if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
                    raise ValueError("Production frontend URLs must be reachable by users")
        return self

    @property
    def r2_endpoint_url(self) -> str | None:
        """สร้าง S3 endpoint ของ account เมื่อมี Account ID แล้ว."""
        if not self.r2_account_id:
            return None
        return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"

    # อ่านค่าเพิ่มเติมจากไฟล์ .env โดยชื่อ environment variable ไม่สนตัวพิมพ์
    model_config = SettingsConfigDict(
        env_file=_environment_files(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        hide_input_in_errors=True,
        extra="ignore",  # Shared dotenv also contains Compose/frontend variables.
    )


@lru_cache
def get_settings() -> Settings:
    """สร้าง Settings ครั้งเดียวแล้วใช้ซ้ำตลอดอายุ process."""
    return Settings()


settings = get_settings()
