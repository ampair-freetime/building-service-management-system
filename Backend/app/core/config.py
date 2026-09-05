"""ค่าตั้งต้นของ backend ซึ่งสามารถแทนที่ได้ด้วย environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Cloudflare R2 ใช้ S3-compatible API โดย credentials ต้องอยู่ฝั่ง backend เท่านั้น
    r2_account_id: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket_name: str | None = None
    r2_presigned_url_expire_seconds: int = 900

    # จำกัดทั้งขนาดไฟล์และจำนวน pixel เพื่อลดความเสี่ยงจากไฟล์ภาพผิดปกติ
    max_image_upload_bytes: int = 5 * 1024 * 1024
    max_image_pixels: int = 25_000_000

    @property
    def r2_endpoint_url(self) -> str | None:
        """สร้าง S3 endpoint ของ account เมื่อมี Account ID แล้ว."""
        if not self.r2_account_id:
            return None
        return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"

    # อ่านค่าเพิ่มเติมจากไฟล์ .env โดยชื่อ environment variable ไม่สนตัวพิมพ์
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    """สร้าง Settings ครั้งเดียวแล้วใช้ซ้ำตลอดอายุ process."""
    return Settings()


settings = get_settings()
