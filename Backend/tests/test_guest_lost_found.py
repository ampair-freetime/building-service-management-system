import asyncio
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image as PillowImage
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.dependencies import provide_object_storage
from app.models.enums import LostStatus, LostType
from app.models.image import Image
from app.models.lost_found import LostItem
from app.services.object_storage import StorageOperationError, StoredObject


class FakeObjectStorage:
    """R2 ตัวปลอมสำหรับยืนยัน flow โดยไม่เรียก network จริง."""

    bucket_name = "test-images"

    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.fail_put = False

    async def put(
        self,
        *,
        object_key: str,
        data: bytes,
        content_type: str,
    ) -> StoredObject:
        if self.fail_put:
            raise StorageOperationError("simulated R2 failure")
        self.objects[object_key] = (data, content_type)
        return StoredObject(
            object_key=object_key,
            bucket_name=self.bucket_name,
            etag="fake-etag",
        )

    async def delete(self, object_key: str) -> None:
        self.objects.pop(object_key, None)

    def create_download_url(self, object_key: str) -> str:
        return f"https://signed.example/{object_key}?expires=900"


@pytest.fixture
def fake_storage(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> FakeObjectStorage:
    client, _ = test_context
    storage = FakeObjectStorage()
    client.app.dependency_overrides[provide_object_storage] = lambda: storage
    yield storage
    client.app.dependency_overrides.pop(provide_object_storage, None)


def make_png() -> bytes:
    output = BytesIO()
    PillowImage.new("RGB", (32, 24), color=(30, 120, 200)).save(
        output,
        format="PNG",
    )
    return output.getvalue()


def lost_form() -> dict[str, str]:
    return {
        "item_category": "อุปกรณ์อิเล็กทรอนิกส์",
        "item_name": "โทรศัพท์สีดำ",
        "description": "มีรอยที่มุมเครื่อง",
        "event_datetime": "2025-01-15T10:30:00",
        "location_detail": "อาคาร C ห้อง 104",
        "reporter_email": "GUEST@EXAMPLE.COM",
    }


def found_form() -> dict[str, str]:
    return {
        "item_category": "กุญแจ",
        "item_name": "กุญแจพร้อมพวงสีแดง",
        "description": "พบหน้าห้องสมุด",
        "event_datetime": "2025-01-15T11:00:00",
        "location_detail": "อาคารหอสมุด ชั้น 1",
        "custody_location": "ห้องประชาสัมพันธ์",
        "private_verification_detail": "มีลูกกุญแจสามดอกและหมายเลขด้านหลัง",
        "reporter_email": "finder@example.com",
    }


def test_guest_creates_lost_item_and_image_is_normalized_to_r2(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    client, session_factory = test_context

    response = client.post(
        "/api/v1/guest/lost-items",
        data=lost_form(),
        files={"image": ("phone.png", make_png(), "image/png")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["report_type"] == "lost"
    assert body["status"] == "pending"
    assert body["item_code"].startswith("LOST-")
    assert len(fake_storage.objects) == 1

    object_key, (stored_data, content_type) = next(iter(fake_storage.objects.items()))
    assert object_key.startswith("lost-found/lost/")
    assert object_key.endswith(".webp")
    assert content_type == "image/webp"
    assert stored_data.startswith(b"RIFF")

    async def read_rows() -> tuple[LostItem, Image]:
        async with session_factory() as session:
            item = await session.scalar(
                select(LostItem).where(LostItem.item_code == body["item_code"])
            )
            image = await session.scalar(select(Image).where(Image.lost_item_id == item.id))
            assert item is not None
            assert image is not None
            return item, image

    item, image = asyncio.run(read_rows())
    assert item.reporter_email == "guest@example.com"
    assert item.report_type == LostType.LOST
    assert image.object_key == object_key
    assert image.bucket_name == "test-images"
    assert image.etag == "fake-etag"
    assert image.width == 32
    assert image.height == 24
    assert image.purge_after is None


def test_public_list_only_returns_approved_items_and_hides_private_fields(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    client, session_factory = test_context
    created = client.post(
        "/api/v1/guest/found-items",
        data=found_form(),
        files={"image": ("keys.png", make_png(), "image/png")},
    )
    assert created.status_code == 201
    item_code = created.json()["item_code"]

    pending_list = client.get("/api/v1/guest/found-items")
    assert pending_list.status_code == 200
    assert pending_list.json()["total"] == 0

    async def approve_item() -> None:
        async with session_factory() as session:
            item = await session.scalar(select(LostItem).where(LostItem.item_code == item_code))
            assert item is not None
            item.status = LostStatus.APPROVED
            await session.commit()

    asyncio.run(approve_item())

    approved_list = client.get(
        "/api/v1/guest/found-items",
        params={"search": "กุญแจ"},
    )
    assert approved_list.status_code == 200
    body = approved_list.json()
    assert body["total"] == 1
    public_item = body["items"][0]
    assert public_item["item_code"] == item_code
    assert public_item["custody_location"] == "ห้องประชาสัมพันธ์"
    assert public_item["images"][0]["url"].startswith("https://signed.example/lost-found/found/")
    assert "reporter_email" not in public_item
    assert "private_verification_detail" not in public_item

    detail = client.get(f"/api/v1/guest/found-items/{item_code.lower()}")
    assert detail.status_code == 200
    assert detail.json()["item_code"] == item_code


def test_found_item_keeps_verification_detail_private_in_database(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    client, session_factory = test_context
    response = client.post("/api/v1/guest/found-items", data=found_form())

    assert response.status_code == 201
    assert fake_storage.objects == {}
    item_code = response.json()["item_code"]

    async def read_item() -> LostItem:
        async with session_factory() as session:
            item = await session.scalar(select(LostItem).where(LostItem.item_code == item_code))
            assert item is not None
            return item

    item = asyncio.run(read_item())
    assert item.report_type == LostType.FOUND
    assert item.private_verification_detail == "มีลูกกุญแจสามดอกและหมายเลขด้านหลัง"


@pytest.mark.parametrize(
    ("filename", "content", "content_type"),
    [
        ("fake.png", b"this-is-not-an-image", "image/png"),
        ("photo.gif", b"GIF89a", "image/gif"),
    ],
)
def test_invalid_image_is_rejected_without_creating_database_row(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
    filename: str,
    content: bytes,
    content_type: str,
) -> None:
    client, session_factory = test_context
    response = client.post(
        "/api/v1/guest/lost-items",
        data=lost_form(),
        files={"image": (filename, content, content_type)},
    )

    assert response.status_code == 422
    assert fake_storage.objects == {}

    async def count_items() -> int:
        async with session_factory() as session:
            count = await session.scalar(select(func.count(LostItem.id)))
            return int(count or 0)

    assert asyncio.run(count_items()) == 0


def test_r2_failure_does_not_create_database_row(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    client, session_factory = test_context
    fake_storage.fail_put = True

    response = client.post(
        "/api/v1/guest/lost-items",
        data=lost_form(),
        files={"image": ("phone.png", make_png(), "image/png")},
    )

    assert response.status_code == 502

    async def count_items() -> int:
        async with session_factory() as session:
            count = await session.scalar(select(func.count(LostItem.id)))
            return int(count or 0)

    assert asyncio.run(count_items()) == 0


def test_owner_tracks_pending_item_that_public_cannot_see(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    client, _ = test_context
    created = client.post("/api/v1/guest/lost-items", data=lost_form())
    assert created.status_code == 201
    item_code = created.json()["item_code"]

    # ไม่ส่งอีเมล = โหมด public ซึ่งยังไม่เห็นประกาศที่รอตรวจสอบ
    assert client.get(f"/api/v1/guest/lost-items/{item_code}").status_code == 404

    # ส่งอีเมลผู้แจ้ง = โหมดติดตาม เห็นประกาศของตัวเองแม้ยังไม่อนุมัติ
    tracked = client.get(
        f"/api/v1/guest/lost-items/{item_code.lower()}",
        params={"reporter_email": "GUEST@EXAMPLE.COM"},
    )
    assert tracked.status_code == 200
    body = tracked.json()
    assert body["item_code"] == item_code
    assert body["status"] == "pending"
    assert "reporter_email" not in body
    assert "private_verification_detail" not in body


def test_tracking_does_not_reveal_whether_reporter_email_matches(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    client, _ = test_context
    item_code = client.post("/api/v1/guest/lost-items", data=lost_form()).json()["item_code"]

    wrong_email = client.get(
        f"/api/v1/guest/lost-items/{item_code}",
        params={"reporter_email": "someone-else@example.com"},
    )
    unknown_code = client.get(
        "/api/v1/guest/lost-items/LOST-20250101-DEADBEEF",
        params={"reporter_email": "guest@example.com"},
    )
    # ตอบเหมือนกันเป๊ะ เพื่อไม่ให้ใช้ endpoint นี้ไล่เดาอีเมลผู้แจ้งได้
    assert wrong_email.status_code == unknown_code.status_code == 404
    assert wrong_email.json() == unknown_code.json()

    # รหัสของประกาศของหายต้องดูผ่าน namespace ของหายเท่านั้น
    crossed = client.get(
        f"/api/v1/guest/found-items/{item_code}",
        params={"reporter_email": "guest@example.com"},
    )
    assert crossed.status_code == 404

    malformed = client.get(
        f"/api/v1/guest/lost-items/{item_code}",
        params={"reporter_email": "not-an-email"},
    )
    assert malformed.status_code == 422
