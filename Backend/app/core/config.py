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
        "postgresql+asyncpg://building_service:building_service"
        "@localhost:5432/building_service"
    )

    # production ต้องกำหนด JWT_SECRET_KEY ใหม่ผ่าน environment variable
    jwt_secret_key: str = "development-only-change-this-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # อ่านค่าเพิ่มเติมจากไฟล์ .env โดยชื่อ environment variable ไม่สนตัวพิมพ์
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    """สร้าง Settings ครั้งเดียวแล้วใช้ซ้ำตลอดอายุ process."""
    return Settings()


settings = get_settings()
