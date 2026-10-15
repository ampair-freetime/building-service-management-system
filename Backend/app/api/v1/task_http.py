"""ตัวช่วยร่วมของ router แม่บ้านและช่าง: แปลง error ของ task_lifecycle เป็น HTTP แบบเดียวกัน."""

from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import HTTPException, status

from app.models.image import Image
from app.models.service_request import ServiceRequest
from app.services.images import InvalidImageError
from app.services.object_storage import StorageOperationError
from app.services.task_lifecycle import (
    TaskConflictError,
    TaskNotFoundError,
    TaskNotOwnedError,
)


@contextmanager
def task_http_errors() -> Iterator[None]:
    """ครอบการเรียก task_lifecycle; ทุก endpoint ได้ status code ชุดเดียวกัน."""
    try:
        yield
    except TaskNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TaskNotOwnedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TaskConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except StorageOperationError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, detail="ไม่สามารถอัปโหลดรูปภาพได้"
        ) from exc
    except (InvalidImageError, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc


def visible_images(task: ServiceRequest) -> list[Image]:
    """รูปที่ยังไม่ถูกลบ เรียงตาม sort_order (รูปไม่มีลำดับไว้ท้าย) แล้วตามเวลาอัป."""
    return sorted(
        (image for image in task.images if image.deleted_at is None),
        key=lambda image: (image.sort_order is None, image.sort_order or 0, image.created_at),
    )
