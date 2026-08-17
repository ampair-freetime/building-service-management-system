"""Cloudflare R2 adapter ที่ซ่อนรายละเอียดของ S3-compatible API จาก business logic."""

from dataclasses import dataclass
from functools import lru_cache

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi.concurrency import run_in_threadpool

from app.core.config import Settings, settings


class StorageConfigurationError(RuntimeError):
    """R2 credentials หรือชื่อ bucket ยังตั้งค่าไม่ครบ."""


class StorageOperationError(RuntimeError):
    """R2 ปฏิเสธคำสั่งหรือไม่สามารถเชื่อมต่อได้."""


@dataclass(frozen=True)
class StoredObject:
    """ผลลัพธ์ขั้นต่ำที่ต้องเก็บหลัง upload สำเร็จ."""

    object_key: str
    bucket_name: str
    etag: str | None


class ObjectStorage:
    """จัดการ object ใน private R2 bucket ผ่าน boto3."""

    def __init__(self, configuration: Settings) -> None:
        required = {
            "R2_ACCOUNT_ID": configuration.r2_account_id,
            "R2_ACCESS_KEY_ID": configuration.r2_access_key_id,
            "R2_SECRET_ACCESS_KEY": configuration.r2_secret_access_key,
            "R2_BUCKET_NAME": configuration.r2_bucket_name,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise StorageConfigurationError(f"Missing R2 configuration: {', '.join(missing)}")

        endpoint_url = configuration.r2_endpoint_url
        if endpoint_url is None:
            raise StorageConfigurationError("Missing R2 endpoint URL")

        self.bucket_name = str(configuration.r2_bucket_name)
        self.presigned_url_expire_seconds = configuration.r2_presigned_url_expire_seconds
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=configuration.r2_access_key_id,
            aws_secret_access_key=configuration.r2_secret_access_key,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    async def put(
        self,
        *,
        object_key: str,
        data: bytes,
        content_type: str,
    ) -> StoredObject:
        """อัปโหลด byte ที่ผ่านการตรวจแล้ว โดยไม่ block event loop ของ FastAPI."""
        try:
            response = await run_in_threadpool(
                self._client.put_object,
                Bucket=self.bucket_name,
                Key=object_key,
                Body=data,
                ContentType=content_type,
                ContentLength=len(data),
                CacheControl="private, no-store",
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageOperationError("Unable to upload image to R2") from exc

        etag = response.get("ETag")
        return StoredObject(
            object_key=object_key,
            bucket_name=self.bucket_name,
            etag=etag.strip('"') if isinstance(etag, str) else None,
        )

    async def delete(self, object_key: str) -> None:
        """ลบ object ใช้สำหรับชดเชยเมื่อ database commit ไม่สำเร็จ."""
        try:
            await run_in_threadpool(
                self._client.delete_object,
                Bucket=self.bucket_name,
                Key=object_key,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageOperationError("Unable to delete image from R2") from exc

    def create_download_url(self, object_key: str) -> str:
        """สร้าง URL ชั่วคราวสำหรับอ่าน object ใน private bucket."""
        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=self.presigned_url_expire_seconds,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageOperationError("Unable to create image download URL") from exc


@lru_cache
def get_object_storage() -> ObjectStorage:
    """ใช้ R2 client ชุดเดียวตลอดอายุ process."""
    return ObjectStorage(settings)
