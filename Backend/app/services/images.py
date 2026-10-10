"""ตรวจและแปลงรูปจาก guest ก่อนส่งไป object storage."""

import asyncio
import warnings
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO

import anyio
from fastapi import UploadFile
from PIL import Image as PillowImage
from PIL import ImageOps, UnidentifiedImageError

from app.core.config import settings

ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
OUTPUT_CONTENT_TYPE = "image/webp"
MAX_WEBP_DIMENSION = 16383


@lru_cache
def _processing_limiter() -> anyio.CapacityLimiter:
    """Limit decoded-image memory per worker; queued calls have not read bytes yet."""
    return anyio.CapacityLimiter(settings.max_image_processing_concurrency)


class InvalidImageError(ValueError):
    """ไฟล์ไม่ใช่รูปที่ระบบรองรับ หรือเกินขอบเขตความปลอดภัย."""


@dataclass(frozen=True)
class ProcessedImage:
    """รูป WebP ที่ตัด metadata แล้ว พร้อมข้อมูลสำหรับบันทึกฐานข้อมูล."""

    data: bytes
    content_type: str
    width: int
    height: int


async def prepare_guest_image(upload: UploadFile) -> ProcessedImage:
    """Keep a worker's capacity token until decoding finishes, even after cancellation."""
    job = asyncio.create_task(_prepare_limited_image(upload))
    try:
        return await asyncio.shield(job)
    except asyncio.CancelledError:
        # Python cannot stop a running thread. Let its owner finish and release the
        # token before propagating cancellation; repeated cancellation stays safe.
        with anyio.CancelScope(shield=True):
            while not job.done():
                try:
                    await asyncio.shield(job)
                except asyncio.CancelledError:
                    continue
                except Exception:  # noqa: BLE001 - Preserve cancellation after worker cleanup.
                    break
        if not job.cancelled():
            job.exception()  # Retrieve a worker failure without masking cancellation.
        raise


async def _prepare_limited_image(upload: UploadFile) -> ProcessedImage:
    """Read bounded bytes and normalize under a per-process capacity limiter."""
    if upload.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise InvalidImageError("รองรับเฉพาะไฟล์ JPG, PNG หรือ WebP")

    try:
        # Keep the token until the thread finishes, including request cancellation.
        async with _processing_limiter():
            data = await upload.read(settings.max_image_upload_bytes + 1)
            if not data:
                raise InvalidImageError("ไฟล์รูปภาพว่างเปล่า")
            if len(data) > settings.max_image_upload_bytes:
                raise InvalidImageError("รูปภาพมีขนาดเกินกำหนด")
            with anyio.CancelScope(shield=True):
                return await anyio.to_thread.run_sync(
                    _normalize_to_webp,
                    data,
                    settings.max_image_output_bytes,
                    settings.max_image_pixels,
                    settings.image_max_dimension,
                    settings.image_webp_quality,
                )
    finally:
        await upload.close()


def _quality_ladder(quality: int) -> list[int]:
    """quality ที่ตั้งไว้ก่อน แล้วค่อยลดลง โดยไม่ต่ำกว่า 50 เพื่อให้ยังอ่านรายละเอียดได้."""
    return [quality, *(step for step in (70, 60, 50) if step < quality)]


def _normalize_to_webp(
    data: bytes,
    max_output_bytes: int,
    max_pixels: int,
    max_dimension: int = 2048,
    quality: int = 78,
) -> ProcessedImage:
    """ตรวจเนื้อหาไฟล์จริง หมุนตาม EXIF ย่อด้านยาว แล้ว encode ใหม่เพื่อตัด metadata."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", PillowImage.DecompressionBombWarning)
            with PillowImage.open(BytesIO(data)) as source:
                if source.format not in ALLOWED_IMAGE_FORMATS:
                    raise InvalidImageError("เนื้อหาไฟล์ไม่ใช่รูป JPG, PNG หรือ WebP")
                if getattr(source, "n_frames", 1) != 1:
                    raise InvalidImageError("ยังไม่รองรับรูปภาพเคลื่อนไหว")

                width, height = source.size
                if width <= 0 or height <= 0 or width * height > max_pixels:
                    raise InvalidImageError("รูปภาพมีความละเอียดสูงเกินกำหนด")
                # JPEG ให้ libjpeg decode แบบย่อ 1/2–1/8 ตั้งแต่ตอนแตกไฟล์ (ต้องเรียกก่อน load)
                # รูป 50MP จะใช้ RAM ไม่กี่ MB แทนที่จะเป็น ~150MB เมื่อ decode เต็มขนาด
                # ขนาดที่ได้จะไม่เล็กกว่า max_dimension จึงยังย่อละเอียดต่อด้วย thumbnail ได้
                if source.format == "JPEG":
                    source.draft("RGB", (max_dimension, max_dimension))
                source.load()
                normalized = ImageOps.exif_transpose(source)
                target_mode = "RGBA" if "A" in normalized.getbands() else "RGB"
                normalized = normalized.convert(target_mode)
                # thumbnail คงสัดส่วนและไม่ขยายรูปที่เล็กกว่าอยู่แล้ว (แก้ภาพในที่ ไม่คืนค่า)
                normalized.thumbnail(
                    (max_dimension, max_dimension),
                    PillowImage.Resampling.LANCZOS,
                    reducing_gap=3.0,
                )
                # ต้องอ่านขนาดใหม่หลัง exif_transpose และ thumbnail เพราะภาพที่ถูกหมุน
                # 90/270 องศาจะสลับด้านกว้าง-สูง ถ้าใช้ width/height จาก source เดิม
                # ค่าที่บันทึกลง DB จะไม่ตรงกับไฟล์ WebP จริงที่ถูกเก็บใน R2
                width, height = normalized.size
                if width > MAX_WEBP_DIMENSION or height > MAX_WEBP_DIMENSION:
                    raise InvalidImageError(f"รูปภาพแต่ละด้านต้องไม่เกิน {MAX_WEBP_DIMENSION:,} พิกเซล")

                # รูปที่บีบอัดยาก (เช่น noise เยอะ) ลด quality ทีละขั้นจนกว่าจะไม่เกินขนาดที่กำหนด
                for attempt_quality in _quality_ladder(quality):
                    output = BytesIO()
                    normalized.save(
                        output,
                        format="WEBP",
                        quality=attempt_quality,
                        method=6,
                    )
                    if output.tell() <= max_output_bytes:
                        break
    except InvalidImageError:
        raise
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        PillowImage.DecompressionBombError,
        PillowImage.DecompressionBombWarning,
    ) as exc:
        # ValueError ครอบไว้เป็นตาข่ายกันตก (เช่น Pillow ปฏิเสธตอน encode เกินขีดจำกัดของฟอร์แมต)
        # ต้องอยู่หลัง "except InvalidImageError: raise" เสมอ เพราะ InvalidImageError
        # สืบทอดจาก ValueError — ถ้าสลับลำดับ ข้อความ error ที่ตั้งใจเขียนจะถูกกลืนหมด
        raise InvalidImageError("ไม่สามารถอ่านไฟล์รูปภาพนี้ได้") from exc

    encoded = output.getvalue()
    if len(encoded) > max_output_bytes:
        raise InvalidImageError("รูปหลังประมวลผลมีขนาดเกินกำหนด")

    return ProcessedImage(
        data=encoded,
        content_type=OUTPUT_CONTENT_TYPE,
        width=width,
        height=height,
    )
