"""Stable, non-expiring image links that redirect to short-lived R2 links.

The API returns /api/v1/images/{id}?sig=... instead of an R2 presigned URL. The link never
expires, so a page left open (or a lazy-loaded <img>) keeps working, while the bucket stays
private: the endpoint creates a fresh short R2 link every time the browser asks for the file.
"""

import base64
import hashlib
import hmac
from uuid import UUID

from app.core.config import settings


def sign_image_id(image_id: UUID) -> str:
    """HMAC of the image id. Only someone who received a link from the API can know it."""
    digest = hmac.new(
        settings.image_url_secret.encode("utf-8"),
        str(image_id).encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def verify_image_signature(image_id: UUID, signature: str) -> bool:
    # compare_digest keeps the comparison time independent of how many characters match.
    # Encode first: compare_digest raises TypeError for str containing non-ASCII characters.
    return hmac.compare_digest(
        sign_image_id(image_id).encode("utf-8"), signature.encode("utf-8")
    )


def build_image_url(image_id: UUID) -> str:
    return f"{settings.api_v1_prefix}/images/{image_id}?sig={sign_image_id(image_id)}"
