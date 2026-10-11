"""Stable image links: signing helper and the redirect endpoint."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.api.dependencies import provide_object_storage
from app.core.config import settings
from app.models.enums import LostStatus, LostType
from app.models.image import Image
from app.models.lost_found import LostItem
from app.services import image_urls
from app.services.object_storage import StorageOperationError


def test_signature_round_trip_and_tampering():
    image_id = uuid4()
    signature = image_urls.sign_image_id(image_id)

    assert image_urls.verify_image_signature(image_id, signature)
    assert not image_urls.verify_image_signature(image_id, signature[:-1] + "x")
    assert not image_urls.verify_image_signature(image_id, "")
    assert not image_urls.verify_image_signature(image_id, "ลายเซ็นปลอม")
    # A signature is only valid for the image it was made for.
    assert not image_urls.verify_image_signature(uuid4(), signature)


def test_changing_the_secret_invalidates_old_signatures(monkeypatch):
    image_id = uuid4()
    old_signature = image_urls.sign_image_id(image_id)

    monkeypatch.setattr(settings, "image_url_secret", "a-different-secret-" * 3)

    assert not image_urls.verify_image_signature(image_id, old_signature)


def test_built_url_is_relative_and_carries_the_signature():
    image_id = uuid4()

    url = image_urls.build_image_url(image_id)

    assert url == f"/api/v1/images/{image_id}?sig={image_urls.sign_image_id(image_id)}"


class RecordingStorage:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def create_download_url(self, object_key, expires_in=None):
        self.calls.append((object_key, expires_in))
        if self.fail:
            raise StorageOperationError("simulated signing failure")
        return f"https://r2.example/{object_key}?X-Amz-Expires={expires_in}"


def _seed_image(session_factory, *, deleted=False):
    async def seed():
        async with session_factory() as session:
            item = LostItem(
                item_code=f"FOUND-{uuid4().hex[:8].upper()}",
                report_type=LostType.FOUND,
                item_category="Accessories",
                item_name="Wallet",
                description="Brown wallet",
                event_datetime=datetime.now(UTC),
                location_detail="Building B",
                reporter_email="reporter@example.com",
                status=LostStatus.APPROVED,
            )
            session.add(item)
            await session.flush()
            image = Image(
                lost_item_id=item.id,
                object_key=f"lost-found/{item.id}/0.webp",
                content_type="image/webp",
                deleted_at=datetime.now(UTC) if deleted else None,
            )
            session.add(image)
            await session.commit()
            return image.id, image.object_key

    return asyncio.run(seed())


@pytest.fixture
def storage(test_context):
    client, _ = test_context
    fake = RecordingStorage()
    client.app.dependency_overrides[provide_object_storage] = lambda: fake
    yield fake
    client.app.dependency_overrides.pop(provide_object_storage, None)


def test_valid_link_redirects_to_a_fresh_short_lived_r2_link(test_context, storage):
    client, factory = test_context
    image_id, object_key = _seed_image(factory)

    response = client.get(image_urls.build_image_url(image_id), follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == (
        f"https://r2.example/{object_key}?X-Amz-Expires={settings.image_redirect_url_expire_seconds}"
    )
    # The browser must stop reusing the redirect before the R2 link inside it expires.
    max_age = int(response.headers["cache-control"].split("max-age=")[1])
    assert response.headers["cache-control"].startswith("private")
    assert max_age < settings.image_redirect_url_expire_seconds


def test_every_request_creates_a_new_r2_link(test_context, storage):
    client, factory = test_context
    image_id, _ = _seed_image(factory)
    url = image_urls.build_image_url(image_id)

    client.get(url, follow_redirects=False)
    client.get(url, follow_redirects=False)

    assert len(storage.calls) == 2


@pytest.mark.parametrize("query", ["", "?sig=", "?sig=wrong-signature"])
def test_missing_or_wrong_signature_looks_like_a_missing_image(test_context, storage, query):
    client, factory = test_context
    image_id, _ = _seed_image(factory)

    response = client.get(f"/api/v1/images/{image_id}{query}", follow_redirects=False)

    assert response.status_code == 404
    assert storage.calls == []


def test_unknown_image_with_a_valid_signature_is_not_found(test_context, storage):
    client, _ = test_context

    response = client.get(image_urls.build_image_url(uuid4()), follow_redirects=False)

    assert response.status_code == 404
    assert storage.calls == []


def test_deleted_image_is_not_found(test_context, storage):
    client, factory = test_context
    image_id, _ = _seed_image(factory, deleted=True)

    response = client.get(image_urls.build_image_url(image_id), follow_redirects=False)

    assert response.status_code == 404
    assert storage.calls == []


def test_storage_failure_returns_503(test_context):
    client, factory = test_context
    image_id, _ = _seed_image(factory)
    client.app.dependency_overrides[provide_object_storage] = lambda: RecordingStorage(fail=True)
    try:
        response = client.get(image_urls.build_image_url(image_id), follow_redirects=False)
    finally:
        client.app.dependency_overrides.pop(provide_object_storage, None)

    assert response.status_code == 503


def test_unconfigured_storage_returns_503(test_context):
    client, factory = test_context
    image_id, _ = _seed_image(factory)

    response = client.get(image_urls.build_image_url(image_id), follow_redirects=False)

    assert response.status_code == 503
