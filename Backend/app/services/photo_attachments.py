import logging
from dataclasses import dataclass
from types import TracebackType
from typing import Self
from uuid import UUID, uuid4

from fastapi import UploadFile

from app.models.enums import ImageType
from app.models.image import Image
from app.services.images import ProcessedImage, prepare_guest_image
from app.services.object_storage import (
    ObjectStorage,
    StorageConfigurationError,
    StorageOperationError,
    StoredObject,
)

logger = logging.getLogger(__name__)

# ค่าที่เขียนลงคอลัมน์ Image.storage_provider (ตอนนี้มี R2 อย่างเดียว)
STORAGE_PROVIDER = "r2"


@dataclass(frozen=True)
class StagedPhoto:
    """รูปที่อัปขึ้น storage แล้ว แต่ยังไม่มีแถวในฐานข้อมูลอ้างถึง."""

    image_id: UUID
    processed: ProcessedImage
    stored: StoredObject
    sort_order: int


class PhotoBatch:
    """ชุดรูปที่อัปแล้วของคำร้องหนึ่งรายการ จะถูกลบทิ้งเมื่อออกจาก ``async with`` โดยไม่ keep()."""

    def __init__(
        self,
        storage: ObjectStorage | None,
        photos: list[StagedPhoto],
        attempted_keys: list[str],
    ) -> None:
        self._storage = storage
        self.photos = photos
        # รวม key ที่ PUT แล้วล้มเหลวด้วย เพราะ request อาจไปถึง storage แล้วก็ได้
        self._attempted_keys = attempted_keys
        self._kept = False

    def __len__(self) -> int:
        return len(self.photos)

    @property
    def object_keys(self) -> list[str]:
        return [photo.stored.object_key for photo in self.photos]

    def image_rows(
        self,
        *,
        request_id: UUID | None = None,
        lost_item_id: UUID | None = None,
        image_type: ImageType | None = None,
        uploaded_by_staff_id: UUID | None = None,
    ) -> list[Image]:
        """สร้างแถว Image ของทุกรูป ให้ caller ``session.add_all`` ใน transaction ของตัวเอง.

        CheckConstraint image_parent_check: รูปของคำร้อง (request_id) ต้องมี image_type
        ส่วนรูปของ lost item ต้องเป็น NULL
        """
        return [
            Image(
                id=photo.image_id,
                request_id=request_id,
                lost_item_id=lost_item_id,
                object_key=photo.stored.object_key,
                storage_provider=STORAGE_PROVIDER,
                bucket_name=photo.stored.bucket_name,
                content_type=photo.processed.content_type,
                size_bytes=len(photo.processed.data),
                etag=photo.stored.etag,
                width=photo.processed.width,
                height=photo.processed.height,
                sort_order=photo.sort_order,
                image_type=image_type,
                uploaded_by_staff_id=uploaded_by_staff_id,
            )
            for photo in self.photos
        ]

    def keep(self) -> None:
        """เรียกหลัง commit สำเร็จ (หรือเมื่อไม่แน่ใจว่า commit ไปแล้ว) เพื่อไม่ให้ลบไฟล์."""
        self._kept = True

    async def discard(self) -> None:
        """ลบไฟล์ทั้งหมดที่อัปไปแล้ว; ลบไม่สำเร็จแค่ log ไว้ ไม่กลบ error หลักของ caller."""
        if self._kept or self._storage is None:
            return
        keys, self._attempted_keys = self._attempted_keys, []
        for key in keys:
            try:
                await self._storage.delete(key)
            except StorageOperationError:
                logger.exception("Failed to remove orphaned R2 object %s", key)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        # asyncio.CancelledError ก็ผ่านตรงนี้ จึงไม่มีไฟล์ค้างแม้ request ถูกยกเลิกกลางทาง
        if not self._kept:
            await self.discard()


async def stage_photos(
    storage: ObjectStorage | None,
    uploads: list[UploadFile],
    *,
    key_prefix: str,
) -> PhotoBatch:
    """ตรวจและแปลงทุกรูปก่อน แล้วค่อยอัปขึ้น storage ทีละรูป.

    ตรวจครบทุกรูปก่อนอัป เพื่อไม่ให้รูปแรก ๆ ค้างใน storage แล้วค่อยพบว่ารูปท้าย ๆ ใช้ไม่ได้
    ถ้าอัปไม่สำเร็จกลางทาง จะลบรูปที่อัปไปแล้วก่อน raise ต่อ
    """
    if not uploads:
        return PhotoBatch(storage, [], [])
    if storage is None:
        raise StorageConfigurationError("Object storage is not configured")

    processed = [await prepare_guest_image(upload) for upload in uploads]
    batch = PhotoBatch(storage, [], [])
    try:
        for sort_order, photo in enumerate(processed):
            image_id = uuid4()
            key = f"{key_prefix}/{image_id}.webp"
            batch._attempted_keys.append(key)
            stored = await storage.put(
                object_key=key, data=photo.data, content_type=photo.content_type
            )
            batch.photos.append(StagedPhoto(image_id, photo, stored, sort_order))
    except BaseException:
        await batch.discard()
        raise
    return batch
