import asyncio
import concurrent.futures
from datetime import datetime
from io import BytesIO
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from PIL import Image as PillowImage
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.dependencies import provide_object_storage
from app.models.enums import ClaimStatus, LostStatus, LostType
from app.models.image import Image
from app.models.lost_found import LostClaim, LostItem
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


def make_wide_png() -> bytes:
    """20000x1000 = 20 ล้าน pixel รวม (ต่ำกว่าเพดาน 25 ล้าน) แต่ด้านกว้างเกิน
    ขีดจำกัด 16383 px ของฟอร์แมต WebP — ตรวจแค่พื้นที่รวมอย่างเดียวจะจับไม่ได้."""
    output = BytesIO()
    PillowImage.new("RGB", (20_000, 1_000), color=(10, 20, 30)).save(output, format="PNG")
    return output.getvalue()


def make_rotated_jpeg() -> bytes:
    """JPEG แนวตั้ง 400x1200 ติด EXIF orientation=6 (หมุน 90 องศาตามเข็ม)
    ไฟล์ที่ decode แล้วหมุนจริงจะกลายเป็น 1200x400."""
    output = BytesIO()
    image = PillowImage.new("RGB", (400, 1200), color=(200, 60, 60))
    exif = image.getexif()
    exif[274] = 6  # 274 = Orientation tag
    image.save(output, format="JPEG", exif=exif)
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
    assert public_item["images"][0]["url"].startswith("https://signed.example/lost-found/found/")
    assert "reporter_email" not in public_item
    assert "private_verification_detail" not in public_item
    # ที่เก็บของต้องไม่หลุดสู่ public ไม่งั้นคนเดินไปเอาเองได้โดยข้าม flow claim
    assert "custody_location" not in public_item

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


def test_extremely_wide_image_is_rejected_with_422(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    """รูปที่ด้านใดด้านหนึ่งเกิน 16383 px ต้องได้ 422 ที่อ่านรู้เรื่อง ไม่ใช่ 500 จาก
    Pillow ตอน encode WebP ล้มเหลว — การตรวจแค่ width*height เทียบเพดานพื้นที่รวม
    ปล่อยรูปยาวเรียวแบบนี้หลุดผ่านไปได้."""
    client, session_factory = test_context
    response = client.post(
        "/api/v1/guest/lost-items",
        data=lost_form(),
        files={"image": ("panorama.png", make_wide_png(), "image/png")},
    )

    assert response.status_code == 422
    assert fake_storage.objects == {}

    async def count_items() -> int:
        async with session_factory() as session:
            count = await session.scalar(select(func.count(LostItem.id)))
            return int(count or 0)

    assert asyncio.run(count_items()) == 0


def test_exif_rotated_image_reports_saved_dimensions(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    """width/height ที่บันทึกลง DB ต้องตรงกับไฟล์ WebP จริงหลังหมุนตาม EXIF
    ไม่ใช่ขนาดดิบก่อนหมุนที่อ่านมาตอนต้น ไม่งั้น frontend ที่ใช้ค่านี้จองพื้นที่
    แสดงผลจะจองผิดด้าน."""
    client, session_factory = test_context
    response = client.post(
        "/api/v1/guest/lost-items",
        data=lost_form(),
        files={"image": ("rotated.jpg", make_rotated_jpeg(), "image/jpeg")},
    )

    assert response.status_code == 201
    item_code = response.json()["item_code"]

    async def read_image() -> Image:
        async with session_factory() as session:
            item = await session.scalar(
                select(LostItem).where(LostItem.item_code == item_code)
            )
            image = await session.scalar(select(Image).where(Image.lost_item_id == item.id))
            assert image is not None
            return image

    image = asyncio.run(read_image())
    # ไฟล์ต้นทางถือกล้องแนวตั้ง 400x1200 แต่ EXIF บอกให้หมุน 90 องศา
    # หลังหมุนจริงจะกลายเป็น 1200x400 — ถ้าโค้ดยังอ่าน source.size ก่อนหมุน
    # ค่าที่ได้จะสลับกันเป็น (400, 1200)
    assert (image.width, image.height) == (1200, 400)


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


def claim_form() -> dict[str, str]:
    return {
        "claimant_name": "สมชาย  ใจดี",
        "claimant_email": "Claimant@Example.COM",
        "proof_detail": "พวงกุญแจมีหมายเลข 1042 สลักด้านหลัง",
    }


def _create_found_item(client: TestClient) -> str:
    response = client.post("/api/v1/guest/found-items", data=found_form())
    assert response.status_code == 201
    return response.json()["item_code"]


def _set_item_status(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    item_code: str,
    new_status: LostStatus,
) -> None:
    """เลื่อนสถานะให้ตรงกับที่เจ้าหน้าที่จะทำ โดยไม่ต้องรอ staff endpoint ที่ยังไม่มี."""

    async def update() -> None:
        async with session_factory() as session:
            item = await session.scalar(
                select(LostItem).where(LostItem.item_code == item_code)
            )
            assert item is not None
            item.status = new_status
            await session.commit()

    asyncio.run(update())


def _read_claims(
    session_factory: async_sessionmaker[AsyncSession],
) -> list[LostClaim]:
    async def read() -> list[LostClaim]:
        async with session_factory() as session:
            result = await session.scalars(select(LostClaim))
            return list(result)

    return asyncio.run(read())


def test_guest_claims_approved_found_item_creates_pending_row(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    client, session_factory = test_context
    item_code = _create_found_item(client)
    _set_item_status(session_factory, item_code=item_code, new_status=LostStatus.APPROVED)

    response = client.post(
        f"/api/v1/guest/found-items/{item_code.lower()}/claims",
        json=claim_form(),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["found_item_code"] == item_code
    assert body["status"] == ClaimStatus.PENDING.value
    assert body["created_at"] is not None

    claims = _read_claims(session_factory)
    assert len(claims) == 1
    claim = claims[0]
    assert claim.status == ClaimStatus.PENDING
    assert claim.reviewed_by is None
    assert claim.review_note is None
    # normalize ต้องทำงาน ไม่งั้นตรวจ claim ซ้ำด้วยอีเมลจะพลาด
    assert claim.claimant_email == "claimant@example.com"
    assert claim.claimant_name == "สมชาย ใจดี"


def test_claim_response_does_not_leak_private_item_fields(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    client, session_factory = test_context
    item_code = _create_found_item(client)
    _set_item_status(session_factory, item_code=item_code, new_status=LostStatus.APPROVED)

    response = client.post(
        f"/api/v1/guest/found-items/{item_code}/claims",
        json=claim_form(),
    )

    assert response.status_code == 201
    body = response.json()
    for leaked in (
        "custody_location",
        "private_verification_detail",
        "reporter_email",
        "review_note",
        "reviewed_by",
    ):
        assert leaked not in body


def test_claim_on_pending_item_returns_404(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    client, session_factory = test_context
    item_code = _create_found_item(client)

    response = client.post(
        f"/api/v1/guest/found-items/{item_code}/claims",
        json=claim_form(),
    )

    assert response.status_code == 404
    assert _read_claims(session_factory) == []


def test_claim_on_lost_item_code_returns_404(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    client, session_factory = test_context
    created = client.post("/api/v1/guest/lost-items", data=lost_form())
    assert created.status_code == 201
    item_code = created.json()["item_code"]
    _set_item_status(session_factory, item_code=item_code, new_status=LostStatus.APPROVED)

    response = client.post(
        f"/api/v1/guest/found-items/{item_code}/claims",
        json=claim_form(),
    )

    assert response.status_code == 404
    assert _read_claims(session_factory) == []


def test_claim_on_already_claimed_item_returns_409(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    client, session_factory = test_context
    item_code = _create_found_item(client)
    _set_item_status(session_factory, item_code=item_code, new_status=LostStatus.CLAIMED)

    response = client.post(
        f"/api/v1/guest/found-items/{item_code}/claims",
        json=claim_form(),
    )

    assert response.status_code == 409
    assert _read_claims(session_factory) == []


def test_duplicate_pending_claim_from_same_email_returns_409(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    client, session_factory = test_context
    item_code = _create_found_item(client)
    _set_item_status(session_factory, item_code=item_code, new_status=LostStatus.APPROVED)

    first = client.post(
        f"/api/v1/guest/found-items/{item_code}/claims",
        json=claim_form(),
    )
    assert first.status_code == 201

    # ตัวพิมพ์ต่างกันต้องยังนับเป็นคนเดียวกัน
    payload = claim_form() | {"claimant_email": "claimant@example.com"}
    second = client.post(
        f"/api/v1/guest/found-items/{item_code}/claims",
        json=payload,
    )

    assert second.status_code == 409
    assert len(_read_claims(session_factory)) == 1


def test_race_between_concurrent_claims_is_rejected_at_the_database(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """สอง request ที่แข่งกันยื่น claim อีเมลเดียวกันพร้อมกัน (เช่น ผู้ใช้กดปุ่มส่งซ้ำ)
    อาจเห็นผล SELECT ตรวจซ้ำว่า "ยังไม่มี" ทั้งคู่ ก่อนที่อีกฝั่งจะ commit ทัน — จำลอง
    จังหวะนั้นด้วยการแทรกคำขอคู่แข่งเข้าไปพอดีตอนที่ dedup SELECT วิ่งผ่านไปแล้วแต่ยัง
    ไม่ทันโยน error ยืนยันว่า partial unique index ที่ DB จับได้ และ service แปลง
    IntegrityError เป็น 409 ไม่ใช่ 500 (ต้องดัก IntegrityError ก่อน SQLAlchemyError
    เพราะเป็นชนิดย่อยของมัน)."""
    client, session_factory = test_context
    item_code = _create_found_item(client)
    _set_item_status(session_factory, item_code=item_code, new_status=LostStatus.APPROVED)

    async def load_item_id() -> UUID:
        async with session_factory() as session:
            item = await session.scalar(select(LostItem).where(LostItem.item_code == item_code))
            assert item is not None
            return item.id

    found_item_id = asyncio.run(load_item_id())

    original_scalar = AsyncSession.scalar
    injected = {"done": False}

    async def scalar_that_misses_a_concurrent_insert(self, statement, *args, **kwargs):
        result = await original_scalar(self, statement, *args, **kwargs)
        # กรองเฉพาะ SELECT ตรวจ claim ซ้ำใน lost_found_claim.py ไม่แตะ query อื่น
        # เช่น select(LostItem)... ของ _load_found_item
        if (
            not injected["done"]
            and result is None
            and "lost_claims.id" in str(statement).lower()
        ):
            injected["done"] = True
            async with session_factory() as racer:
                racer.add(
                    LostClaim(
                        id=uuid4(),
                        found_item_id=found_item_id,
                        claimant_name="สมชาย ใจดี",
                        claimant_email="claimant@example.com",
                        proof_detail="แข่งกันยื่นพร้อมกัน",
                        status=ClaimStatus.PENDING,
                    )
                )
                await racer.commit()
        return result

    monkeypatch.setattr(AsyncSession, "scalar", scalar_that_misses_a_concurrent_insert)

    response = client.post(
        f"/api/v1/guest/found-items/{item_code}/claims",
        json=claim_form(),
    )

    assert injected["done"], "การจำลอง race ไม่ทำงาน เทสต์นี้จึงไม่ได้พิสูจน์อะไร"
    assert response.status_code == 409
    assert len(_read_claims(session_factory)) == 1


def test_rejected_claim_does_not_block_a_new_claim_from_the_same_email(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    """partial unique index ต้องครอบเฉพาะสถานะ pending — คนที่เคยถูกปฏิเสธและมี
    หลักฐานเพิ่มต้องยื่นคำขอใหม่ได้ ถ้าทำเป็น unique index ธรรมดา (ไม่มี WHERE) จะบล็อก
    คนกลุ่มนี้ไปตลอดชีวิตโดยไม่ตั้งใจ"""
    client, session_factory = test_context
    item_code = _create_found_item(client)
    _set_item_status(session_factory, item_code=item_code, new_status=LostStatus.APPROVED)

    first = client.post(
        f"/api/v1/guest/found-items/{item_code}/claims",
        json=claim_form(),
    )
    assert first.status_code == 201
    claim_id = UUID(first.json()["id"])

    async def reject_claim() -> None:
        async with session_factory() as session:
            claim = await session.scalar(select(LostClaim).where(LostClaim.id == claim_id))
            assert claim is not None
            claim.status = ClaimStatus.REJECTED
            await session.commit()

    asyncio.run(reject_claim())

    second = client.post(
        f"/api/v1/guest/found-items/{item_code}/claims",
        json=claim_form(),
    )

    assert second.status_code == 201
    claims = _read_claims(session_factory)
    assert len(claims) == 2
    assert {c.status for c in claims} == {ClaimStatus.REJECTED, ClaimStatus.PENDING}


@pytest.mark.parametrize(
    "override",
    [
        {"claimant_name": ""},
        {"claimant_name": "ก" * 151},
        {"proof_detail": "   "},
        {"claimant_email": "not-an-email"},
    ],
)
def test_claim_rejects_invalid_payload(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
    override: dict[str, str],
) -> None:
    client, session_factory = test_context
    item_code = _create_found_item(client)
    _set_item_status(session_factory, item_code=item_code, new_status=LostStatus.APPROVED)

    response = client.post(
        f"/api/v1/guest/found-items/{item_code}/claims",
        json=claim_form() | override,
    )

    assert response.status_code == 422
    assert _read_claims(session_factory) == []


def test_claim_ignores_client_supplied_status(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    client, session_factory = test_context
    item_code = _create_found_item(client)
    _set_item_status(session_factory, item_code=item_code, new_status=LostStatus.APPROVED)

    response = client.post(
        f"/api/v1/guest/found-items/{item_code}/claims",
        json=claim_form() | {"status": "approved", "reviewed_by": str(uuid4())},
    )

    assert response.status_code == 422
    assert _read_claims(session_factory) == []


def test_claim_status_requires_matching_email(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    client, session_factory = test_context
    item_code = _create_found_item(client)
    _set_item_status(session_factory, item_code=item_code, new_status=LostStatus.APPROVED)
    created = client.post(
        f"/api/v1/guest/found-items/{item_code}/claims",
        json=claim_form(),
    )
    assert created.status_code == 201
    claim_id = created.json()["id"]

    owner = client.get(
        f"/api/v1/guest/found-items/{item_code}/claims/{claim_id}",
        params={"claimant_email": "CLAIMANT@example.com"},
    )
    assert owner.status_code == 200
    body = owner.json()
    assert body["status"] == ClaimStatus.PENDING.value
    assert body["item_name"] == "กุญแจพร้อมพวงสีแดง"
    assert "review_note" not in body

    stranger = client.get(
        f"/api/v1/guest/found-items/{item_code}/claims/{claim_id}",
        params={"claimant_email": "someone-else@example.com"},
    )
    assert stranger.status_code == 404
    assert stranger.json()["detail"] == "ไม่พบคำขอนี้"


def test_item_code_uses_bangkok_date_not_utc(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    """ช่วงเที่ยงคืนถึงเจ็ดโมงเช้าไทย วันที่แบบ UTC จะเป็นเมื่อวาน ซึ่งผู้ใช้อ่านแล้วสับสน."""
    client, _ = test_context
    response = client.post("/api/v1/guest/lost-items", data=lost_form())

    assert response.status_code == 201
    expected = datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%Y%m%d")
    assert response.json()["item_code"].split("-")[1] == expected


def build_multipart_with_empty_file(fields: dict[str, str]) -> tuple[bytes, str]:
    """ประกอบ body เองเพราะ httpx ตัด filename= ทิ้งเมื่อชื่อว่าง แต่เบราว์เซอร์ส่ง filename="" มาจริง."""
    boundary = "testboundary"
    parts = []
    for name, value in fields.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'
        )
    parts.append(
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="image"; filename=""\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n\r\n"
    )
    parts.append(f"--{boundary}--\r\n")
    return "".join(parts).encode(), f"multipart/form-data; boundary={boundary}"


def test_empty_file_input_is_treated_as_no_image(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    """input type=file ที่ผู้ใช้ไม่เลือกไฟล์ มาถึงเป็น UploadFile ที่ filename ว่าง ไม่ใช่ None."""
    client, session_factory = test_context
    body, content_type = build_multipart_with_empty_file(lost_form())
    response = client.post(
        "/api/v1/guest/lost-items",
        content=body,
        headers={"Content-Type": content_type},
    )

    assert response.status_code == 201
    assert fake_storage.objects == {}

    async def count_images() -> int:
        async with session_factory() as session:
            count = await session.scalar(select(func.count(Image.id)))
            return int(count or 0)

    assert asyncio.run(count_images()) == 0


def test_category_filter_matches_normalized_value(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    """ตอนสร้างยุบช่องว่างซ้อน ตัวกรองจึงต้องยุบด้วย ไม่งั้นค่าที่ผู้ใช้พิมพ์เกินมากรองไม่เจอ."""
    client, session_factory = test_context
    created = client.post(
        "/api/v1/guest/lost-items",
        data=lost_form() | {"item_category": "ของ  ใช้   ส่วนตัว"},
    )
    assert created.status_code == 201
    item_code = created.json()["item_code"]
    _set_item_status(session_factory, item_code=item_code, new_status=LostStatus.APPROVED)

    exact = client.get(
        "/api/v1/guest/lost-items",
        params={"category": "ของ ใช้ ส่วนตัว"},
    )
    assert exact.json()["total"] == 1

    spaced = client.get(
        "/api/v1/guest/lost-items",
        params={"category": "  ของ   ใช้  ส่วนตัว  "},
    )
    assert spaced.json()["total"] == 1

    unrelated = client.get(
        "/api/v1/guest/lost-items",
        params={"category": "เครื่องประดับ"},
    )
    assert unrelated.json()["total"] == 0


def test_custody_location_appears_only_after_claim_is_approved(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
) -> None:
    client, session_factory = test_context
    item_code = _create_found_item(client)
    _set_item_status(session_factory, item_code=item_code, new_status=LostStatus.APPROVED)
    created = client.post(
        f"/api/v1/guest/found-items/{item_code}/claims",
        json=claim_form(),
    )
    assert created.status_code == 201
    claim_id = created.json()["id"]
    status_url = f"/api/v1/guest/found-items/{item_code}/claims/{claim_id}"
    params = {"claimant_email": "claimant@example.com"}

    pending = client.get(status_url, params=params)
    assert pending.status_code == 200
    assert pending.json()["custody_location"] is None

    async def approve_claim() -> None:
        async with session_factory() as session:
            claim = await session.scalar(select(LostClaim))
            assert claim is not None
            claim.status = ClaimStatus.APPROVED
            await session.commit()

    asyncio.run(approve_claim())

    approved = client.get(status_url, params=params)
    assert approved.status_code == 200
    assert approved.json()["custody_location"] == "ห้องประชาสัมพันธ์"


def test_cancellation_after_upload_still_removes_orphaned_r2_object(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeObjectStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CancelledError สืบทอดจาก BaseException จึงไม่ถูก except SQLAlchemyError จับ.

    ถ้าไม่เก็บกวาดใน finally ไฟล์จะค้างใน R2 โดยไม่มีแถวในฐานข้อมูลอ้างถึงตลอดไป
    """
    client, session_factory = test_context

    def cancel_after_upload(*args: object, **kwargs: object) -> None:
        raise asyncio.CancelledError

    # ระเบิดหลัง storage.put สำเร็จแล้ว แต่ก่อน commit
    monkeypatch.setattr(
        "app.services.lost_found.LostItemHistory",
        cancel_after_upload,
    )

    # portal ของ TestClient แปลง asyncio.CancelledError เป็นตัวของ concurrent.futures
    # ตอนข้ามขอบ event loop ตัว service เห็นของเดิมที่เป็น BaseException
    with pytest.raises(concurrent.futures.CancelledError):
        client.post(
            "/api/v1/guest/lost-items",
            data=lost_form(),
            files={"image": ("phone.png", make_png(), "image/png")},
        )

    assert fake_storage.objects == {}

    async def count_items() -> int:
        async with session_factory() as session:
            count = await session.scalar(select(func.count(LostItem.id)))
            return int(count or 0)

    assert asyncio.run(count_items()) == 0
