"""Stable image links that redirect to a fresh, short-lived R2 link."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.api.dependencies import DbSession, ObjectStorageClient
from app.core.config import settings
from app.models.image import Image
from app.services.image_urls import verify_image_signature
from app.services.object_storage import StorageOperationError

router = APIRouter()

# The browser may reuse a redirect for a while, but it must stop before the R2 link inside
# it expires, otherwise it would follow a stale redirect into a 403.
_CACHE_SAFETY_SECONDS = 60


@router.get("/{image_id}", include_in_schema=False)
async def redirect_to_image(
    image_id: UUID,
    session: DbSession,
    storage: ObjectStorageClient,
    sig: str = Query(default="", max_length=128),
) -> RedirectResponse:
    """No JWT: <img> cannot send headers and guests have none, so the signature is the proof."""
    not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    # A bad signature answers exactly like a missing image, so ids cannot be probed.
    if not sig or not verify_image_signature(image_id, sig):
        raise not_found

    object_key = await session.scalar(
        select(Image.object_key).where(Image.id == image_id, Image.deleted_at.is_(None))
    )
    if object_key is None:
        raise not_found

    expires_in = settings.image_redirect_url_expire_seconds
    try:
        target = storage.create_download_url(object_key, expires_in=expires_in)
    except StorageOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Image storage unavailable"
        ) from exc

    # 302, not 301: a permanent redirect would be remembered with an expired R2 link.
    return RedirectResponse(
        target,
        status_code=status.HTTP_302_FOUND,
        headers={"Cache-Control": f"private, max-age={max(expires_in - _CACHE_SAFETY_SECONDS, 0)}"},
    )
