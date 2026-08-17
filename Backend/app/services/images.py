"""ตรวจและแปลงรูปจาก guest ก่อนส่งไป object storage."""

import warnings
from dataclasses import dataclass
from io import BytesIO

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from PIL import Image as PillowImage
from PIL import ImageOps, UnidentifiedImageError

from app.core.config import settings

ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
OUTPUT_CONTENT_TYPE = "image/webp"


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
    """อ่านไฟล์ไม่เกิน limit แล้วส่งงาน decode/re-encode ไป thread pool."""
    if upload.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise InvalidImageError("รองรับเฉพาะไฟล์ JPG, PNG หรือ WebP")

    data = await upload.read(settings.max_image_upload_bytes + 1)
    await upload.close()

    if not data:
        raise InvalidImageError("ไฟล์รูปภาพว่างเปล่า")
    if len(data) > settings.max_image_upload_bytes:
        raise InvalidImageError("รูปภาพต้องมีขนาดไม่เกิน 5 MB")

    return await run_in_threadpool(
        _normalize_to_webp,
        data,
        settings.max_image_upload_bytes,
        settings.max_image_pixels,
    )


def _normalize_to_webp(
    data: bytes,
    max_output_bytes: int,
    max_pixels: int,
) -> ProcessedImage:
    """ตรวจเนื้อหาไฟล์จริง หมุนตาม EXIF แล้ว encode ใหม่เพื่อตัด metadata."""
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

                source.load()
                normalized = ImageOps.exif_transpose(source)
                target_mode = "RGBA" if "A" in normalized.getbands() else "RGB"
                normalized = normalized.convert(target_mode)

                output = BytesIO()
                normalized.save(
                    output,
                    format="WEBP",
                    quality=82,
                    method=4,
                )
    except InvalidImageError:
        raise
    except (
        UnidentifiedImageError,
        OSError,
        PillowImage.DecompressionBombError,
        PillowImage.DecompressionBombWarning,
    ) as exc:
        raise InvalidImageError("ไม่สามารถอ่านไฟล์รูปภาพนี้ได้") from exc

    encoded = output.getvalue()
    if len(encoded) > max_output_bytes:
        raise InvalidImageError("รูปหลังประมวลผลมีขนาดเกิน 5 MB")

    return ProcessedImage(
        data=encoded,
        content_type=OUTPUT_CONTENT_TYPE,
        width=width,
        height=height,
    )
