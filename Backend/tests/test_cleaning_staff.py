import asyncio
from io import BytesIO

import pytest
from PIL import Image as PillowImage

from conftest import seed_staff
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.dependencies import provide_object_storage
from app.models.enums import ImageType, RequestAction, RequestStatus
from app.models.image import Image
from app.models.location import Location
from app.models.service_request import RequestHistory, ServiceRequest
from app.services.object_storage import StoredObject

class FakeStorage:
    """Object storage ปลอมสำหรับทดสอบ completion photos."""

    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.deleted: list[str] = []

    async def put(
        self,
        *,
        object_key: str,
        data: bytes,
        content_type: str,
    ) -> StoredObject:
        self.objects[object_key] = (data, content_type)

        return StoredObject(
            object_key=object_key,
            bucket_name="test-images",
            etag="test-etag",
        )

    async def delete(self, object_key: str) -> None:
        self.deleted.append(object_key)
        self.objects.pop(object_key, None)

    def create_download_url(self, object_key: str) -> str:
        return f"https://example.test/{object_key}"

@pytest.fixture
def fake_storage(test_context) -> FakeStorage:
    client, _ = test_context
    storage = FakeStorage()

    client.app.dependency_overrides[provide_object_storage] = lambda: storage

    yield storage

    client.app.dependency_overrides.pop(provide_object_storage, None)


def make_png() -> bytes:
    output = BytesIO()

    PillowImage.new(
        "RGB",
        (32, 24),
        color="blue",
    ).save(output, format="PNG")

    return output.getvalue()

def seed_location(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def seed() -> None:
        async with session_factory() as session:
            session.add(
                Location(
                    id=1,
                    floor="2",
                    area="ห้อง 201",
                    qr_token="cleaning-staff-test",
                )
            )
            await session.commit()

    asyncio.run(seed())


def login_staff(
    client: TestClient,
    identifier: str,
    password: str,
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": identifier,
            "password": password,
        },
    )

    assert response.status_code == 200

    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }


def get_request_id(
    session_factory: async_sessionmaker[AsyncSession],
    request_code: str,
):
    async def get_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(
                    ServiceRequest.request_code == request_code
                )
            )
            assert request is not None
            return request.id

    return asyncio.run(get_id())


def complete_cleaning_task(
    client: TestClient,
    request_id,
    headers: dict[str, str],
) -> None:
    accepted = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=headers,
    )
    assert accepted.status_code == 200

    for new_status in ("received", "in_progress", "completed"):
        response = client.patch(
            f"/api/v1/cleaning-tasks/{request_id}/status",
            headers=headers,
            json={"status": new_status},
        )
        assert response.status_code == 200
        assert response.json()["status"] == new_status


def test_housekeeper_can_accept_cleaning_task(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="housekeeper1@example.com",
        password="password-one",
        role="housekeeper",
        full_name="House Keeper One",
    )

    headers = login_staff(
        client,
        "housekeeper1@example.com",
        "password-one",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "พื้นเปียก",
            "description": "ข้างลิฟต์ตัวซ้าย",
            "priority": "urgent",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    response = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == str(request_id)
    assert body["request_code"] == created.json()["request_code"]
    assert body["status"] == "assigned"

    assert "staff_code" not in body["assigned_staff"]
    assert body["assigned_staff"]["full_name"] == "House Keeper One"

    async def verify_database() -> None:
        async with session_factory() as session:
            task = await session.get(ServiceRequest, request_id)

            assert task is not None
            assert task.status == RequestStatus.ASSIGNED
            assert task.assigned_staff_id is not None

            history = await session.scalar(
                select(RequestHistory).where(
                    RequestHistory.request_id == request_id,
                    RequestHistory.action == RequestAction.ACCEPTED,
                )
            )

            assert history is not None
            assert history.old_status == RequestStatus.WAITING
            assert history.new_status == RequestStatus.ASSIGNED
            assert history.target_staff_id == task.assigned_staff_id

    asyncio.run(verify_database())


def test_second_housekeeper_cannot_accept_assigned_cleaning_task(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="housekeeper1@example.com",
        password="password-one",
        role="housekeeper",
        full_name="House Keeper One",
    )

    seed_staff(
        session_factory,
        email="housekeeper2@example.com",
        password="password-two",
        role="housekeeper",
        full_name="House Keeper Two",
    )

    hk1_headers = login_staff(
        client,
        "housekeeper1@example.com",
        "password-one",
    )

    hk2_headers = login_staff(
        client,
        "housekeeper2@example.com",
        "password-two",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ถังขยะเต็ม",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    # HK001 รับงานก่อน
    first = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=hk1_headers,
    )

    assert first.status_code == 200
    assert "staff_code" not in first.json()["assigned_staff"]

    # HK002 พยายามรับงานเดียวกัน
    second = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=hk2_headers,
    )

    assert second.status_code == 409
    assert second.json()["detail"] == (
        "Cleaning task has already been assigned"
    )

    # งานต้องยังเป็นของ HK001 และมี ACCEPTED history แค่ครั้งเดียว
    async def verify_database() -> None:
        async with session_factory() as session:
            task = await session.get(ServiceRequest, request_id)

            assert task is not None
            assert task.status == RequestStatus.ASSIGNED

            histories = (
                await session.scalars(
                    select(RequestHistory).where(
                        RequestHistory.request_id == request_id,
                        RequestHistory.action == RequestAction.ACCEPTED,
                    )
                )
            ).all()

            assert len(histories) == 1
            assert histories[0].performed_by == task.assigned_staff_id

    asyncio.run(verify_database())


def test_non_housekeeper_cannot_accept_cleaning_task(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="technician@example.com",
        password="correct-password",
        role="technician",
        full_name="Technician One",
    )

    headers = login_staff(
        client,
        "technician@example.com",
        "correct-password",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "พื้นเปียก",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    response = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Housekeeper access required"


def test_housekeeper_cannot_accept_nonexistent_cleaning_task(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    from uuid import uuid4

    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="housekeeper@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "housekeeper@example.com",
        "correct-password",
    )

    response = client.patch(
        f"/api/v1/cleaning-tasks/{uuid4()}/accept",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cleaning task not found"


def test_housekeeper_can_update_cleaning_status_in_order(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="status-housekeeper@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "status-housekeeper@example.com",
        "correct-password",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ทำความสะอาดพื้น",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    # ก่อนเปลี่ยนสถานะ Cleaner ต้องรับงานก่อน
    accepted = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=headers,
    )

    assert accepted.status_code == 200
    assert accepted.json()["status"] == "assigned"

    # assigned -> received
    received = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/status",
        headers=headers,
        json={"status": "received"},
    )

    assert received.status_code == 200
    assert received.json()["status"] == "received"

    # received -> in_progress
    in_progress = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/status",
        headers=headers,
        json={"status": "in_progress"},
    )

    assert in_progress.status_code == 200
    assert in_progress.json()["status"] == "in_progress"

    # in_progress -> completed
    completed = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/status",
        headers=headers,
        json={"status": "completed"},
    )

    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    # ตรวจสถานะในฐานข้อมูลจริง
    async def verify_database() -> None:
        async with session_factory() as session:
            task = await session.get(ServiceRequest, request_id)

            assert task is not None
            assert task.status == RequestStatus.COMPLETED

    asyncio.run(verify_database())


def test_housekeeper_cannot_skip_cleaning_status(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="invalid-status-housekeeper@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "invalid-status-housekeeper@example.com",
        "correct-password",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "เก็บขยะ",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    accepted = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=headers,
    )

    assert accepted.status_code == 200
    assert accepted.json()["status"] == "assigned"

    # ห้ามข้าม assigned -> completed
    response = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/status",
        headers=headers,
        json={"status": "completed"},
    )

    assert response.status_code == 409

    # หลังถูกปฏิเสธ สถานะต้องยังเป็น assigned
    async def verify_database() -> None:
        async with session_factory() as session:
            task = await session.get(ServiceRequest, request_id)

            assert task is not None
            assert task.status == RequestStatus.ASSIGNED

    asyncio.run(verify_database())


def test_guest_can_view_updated_cleaning_status(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="progress-housekeeper@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "progress-housekeeper@example.com",
        "correct-password",
    )

    reporter_email = "guest@example.com"

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ทำความสะอาดห้อง",
            "description": "ห้อง 201",
            "priority": "normal",
            "reporter_email": reporter_email,
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_code = created.json()["request_code"]
    request_id = get_request_id(session_factory, request_code)

    # Cleaner รับงาน
    accepted = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=headers,
    )
    assert accepted.status_code == 200

    # Cleaner เปลี่ยนเป็น received
    updated = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/status",
        headers=headers,
        json={"status": "received"},
    )

    assert updated.status_code == 200

    # Guest เข้ามาดูคำร้องของตัวเอง
    tracking = client.get(
        f"/api/v1/guest/cleaning-requests/{request_code}",
        params={"reporter_email": reporter_email},
    )

    assert tracking.status_code == 200
    assert tracking.json()["status"] == "received"

    # Cleaner เปลี่ยนต่อเป็น in_progress
    updated = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/status",
        headers=headers,
        json={"status": "in_progress"},
    )

    assert updated.status_code == 200

    # Guest ต้องเห็นสถานะล่าสุด
    tracking = client.get(
        f"/api/v1/guest/cleaning-requests/{request_code}",
        params={"reporter_email": reporter_email},
    )

    assert tracking.status_code == 200
    assert tracking.json()["status"] == "in_progress"


def test_housekeeper_can_upload_completion_photos(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeStorage,
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="photo-housekeeper@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "photo-housekeeper@example.com",
        "correct-password",
    )

    # Guest สร้าง cleaning request
    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ทำความสะอาดพื้น",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    # Cleaner รับงาน
    accepted = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=headers,
    )
    assert accepted.status_code == 200

    # assigned -> received -> in_progress -> completed
    for new_status in ("received", "in_progress", "completed"):
        response = client.patch(
            f"/api/v1/cleaning-tasks/{request_id}/status",
            headers=headers,
            json={"status": new_status},
        )
        assert response.status_code == 200

    # อัปโหลด completion photos 2 รูป
    response = client.post(
        f"/api/v1/cleaning-tasks/{request_id}/completion-photos",
        headers=headers,
        files=[
            ("files", ("after-1.png", make_png(), "image/png")),
            ("files", ("after-2.png", make_png(), "image/png")),
        ],
    )

    assert response.status_code == 200

    body = response.json()

    assert body["request_id"] == str(request_id)
    assert body["image_count"] == 2
    assert len(body["photos"]) == 2

    # รูปถูกแปลงเป็น WebP ก่อนเก็บ
    assert all(
        photo["content_type"] == "image/webp"
        for photo in body["photos"]
    )

    # มีไฟล์อยู่ใน object storage 2 รูป
    assert len(fake_storage.objects) == 2

    async def verify_database() -> None:
        async with session_factory() as session:
            images = (
                await session.scalars(
                    select(Image).where(
                        Image.request_id == request_id,
                        Image.image_type == ImageType.AFTER,
                    )
                )
            ).all()

            assert len(images) == 2

            for image in images:
                assert image.uploaded_by_staff_id is not None
                assert image.content_type == "image/webp"
                assert image.width == 32
                assert image.height == 24

    asyncio.run(verify_database())


def test_invalid_completion_photo_is_not_uploaded(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeStorage,
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="invalid-photo@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "invalid-photo@example.com",
        "correct-password",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ทำความสะอาดพื้น",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    complete_cleaning_task(
        client,
        request_id,
        headers,
    )

    response = client.post(
        f"/api/v1/cleaning-tasks/{request_id}/completion-photos",
        headers=headers,
        files=[
            ("files", ("valid.png", make_png(), "image/png")),
            (
                "files",
                ("invalid.png", b"this is not a real image", "image/png"),
            ),
        ],
    )

    assert response.status_code == 422

    # เพราะ validate รูปทั้งหมดก่อน upload
    # แม้รูปแรกจะถูกต้อง ก็ต้องยังไม่มีอะไรขึ้น storage
    assert len(fake_storage.objects) == 0

    async def verify_database() -> None:
        async with session_factory() as session:
            images = (
                await session.scalars(
                    select(Image).where(
                        Image.request_id == request_id,
                        Image.image_type == ImageType.AFTER,
                    )
                )
            ).all()

            assert len(images) == 0

    asyncio.run(verify_database())


def test_housekeeper_cannot_upload_completion_photos_before_completed(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeStorage,
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="not-completed@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "not-completed@example.com",
        "correct-password",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ทำความสะอาดพื้น",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    # รับงาน
    accepted = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=headers,
    )
    assert accepted.status_code == 200

    # ไปถึงแค่ in_progress ยังไม่ completed
    for new_status in ("received", "in_progress"):
        response = client.patch(
            f"/api/v1/cleaning-tasks/{request_id}/status",
            headers=headers,
            json={"status": new_status},
        )
        assert response.status_code == 200

    # พยายามอัปโหลดรูปก่อนงานเสร็จ
    response = client.post(
        f"/api/v1/cleaning-tasks/{request_id}/completion-photos",
        headers=headers,
        files=[
            ("files", ("after.png", make_png(), "image/png")),
        ],
    )

    assert response.status_code == 409

    # ต้องไม่มีรูปถูก upload
    assert len(fake_storage.objects) == 0


def test_guest_can_view_completion_photos(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeStorage,
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="guest-view-photo@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "guest-view-photo@example.com",
        "correct-password",
    )

    # Guest สร้าง cleaning request
    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ทำความสะอาดพื้น",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_code = created.json()["request_code"]

    request_id = get_request_id(
        session_factory,
        request_code,
    )

    # Cleaner รับงานและทำจนเสร็จ
    complete_cleaning_task(
        client,
        request_id,
        headers,
    )

    # Cleaner อัปโหลดรูปหลังทำงานเสร็จ
    uploaded = client.post(
        f"/api/v1/cleaning-tasks/{request_id}/completion-photos",
        headers=headers,
        files=[
            ("files", ("after-1.png", make_png(), "image/png")),
            ("files", ("after-2.png", make_png(), "image/png")),
        ],
    )

    assert uploaded.status_code == 200
    assert uploaded.json()["image_count"] == 2

    # Guest ติดตามคำร้อง
    tracked = client.get(
        f"/api/v1/guest/cleaning-requests/{request_code}",
        params={
            "reporter_email": "guest@example.com",
        },
    )

    assert tracked.status_code == 200

    body = tracked.json()

    assert body["status"] == "completed"
    assert len(body["completion_photos"]) == 2

    for photo in body["completion_photos"]:
        assert photo["content_type"] == "image/webp"
        assert photo["width"] == 32
        assert photo["height"] == 24
        assert photo["url"].startswith("https://example.test/")


def test_housekeeper_can_add_completion_note(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="completion-note@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "completion-note@example.com",
        "correct-password",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ทำความสะอาดพื้น",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    complete_cleaning_task(
        client,
        request_id,
        headers,
    )

    response = client.post(
        f"/api/v1/cleaning-tasks/{request_id}/completion-note",
        headers=headers,
        json={
            "note": "ทำความสะอาดพื้นและเก็บขยะเรียบร้อยแล้ว",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["request_id"] == str(request_id)
    assert body["note"] == "ทำความสะอาดพื้นและเก็บขยะเรียบร้อยแล้ว"
    assert body["created_at"] is not None

    async def verify_database() -> None:
        async with session_factory() as session:
            history = await session.scalar(
                select(RequestHistory).where(
                    RequestHistory.request_id == request_id,
                    RequestHistory.action
                    == RequestAction.COMPLETION_NOTE_ADDED,
                )
            )

            assert history is not None
            assert history.note == (
                "ทำความสะอาดพื้นและเก็บขยะเรียบร้อยแล้ว"
            )

    asyncio.run(verify_database())


def test_empty_completion_note_is_rejected(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="empty-note@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "empty-note@example.com",
        "correct-password",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ทำความสะอาดพื้น",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    complete_cleaning_task(
        client,
        request_id,
        headers,
    )

    response = client.post(
        f"/api/v1/cleaning-tasks/{request_id}/completion-note",
        headers=headers,
        json={"note": "     "},
    )

    assert response.status_code == 422

    async def verify_database() -> None:
        async with session_factory() as session:
            history = await session.scalar(
                select(RequestHistory).where(
                    RequestHistory.request_id == request_id,
                    RequestHistory.action
                    == RequestAction.COMPLETION_NOTE_ADDED,
                )
            )

            assert history is None

    asyncio.run(verify_database())


def test_housekeeper_cannot_add_completion_note_before_completed(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="note-before-completed@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "note-before-completed@example.com",
        "correct-password",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ทำความสะอาดพื้น",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    accepted = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=headers,
    )

    assert accepted.status_code == 200

    response = client.post(
        f"/api/v1/cleaning-tasks/{request_id}/completion-note",
        headers=headers,
        json={"note": "ยังทำงานไม่เสร็จ"},
    )

    assert response.status_code == 409


def test_other_housekeeper_cannot_add_completion_note(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="owner-note@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="Owner Housekeeper",
    )

    seed_staff(
        session_factory,
        email="other-note@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="Other Housekeeper",
    )

    owner_headers = login_staff(
        client,
        "owner-note@example.com",
        "correct-password",
    )

    other_headers = login_staff(
        client,
        "other-note@example.com",
        "correct-password",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ทำความสะอาดพื้น",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    complete_cleaning_task(
        client,
        request_id,
        owner_headers,
    )

    response = client.post(
        f"/api/v1/cleaning-tasks/{request_id}/completion-note",
        headers=other_headers,
        json={"note": "พยายามเพิ่ม note ของงานคนอื่น"},
    )

    assert response.status_code == 403


def test_completion_note_appears_in_work_history(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="history-note@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "history-note@example.com",
        "correct-password",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ทำความสะอาดพื้น",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    # Cleaner รับงานและทำจน completed
    complete_cleaning_task(
        client,
        request_id,
        headers,
    )

    # บันทึก completion note
    note_response = client.post(
        f"/api/v1/cleaning-tasks/{request_id}/completion-note",
        headers=headers,
        json={
            "note": "ทำความสะอาดพื้นและนำขยะออกเรียบร้อยแล้ว",
        },
    )

    assert note_response.status_code == 200

    # เปิดดู work history
    history_response = client.get(
        f"/api/v1/cleaning-tasks/{request_id}/history",
        headers=headers,
    )

    assert history_response.status_code == 200

    body = history_response.json()

    assert body["request_id"] == str(request_id)

    completion_notes = [
        item
        for item in body["history"]
        if item["action"] == "completion_note_added"
    ]

    assert len(completion_notes) == 1
    assert completion_notes[0]["note"] == (
        "ทำความสะอาดพื้นและนำขยะออกเรียบร้อยแล้ว"
    )
    assert completion_notes[0]["old_status"] == "completed"
    assert completion_notes[0]["new_status"] == "completed"
    assert completion_notes[0]["created_at"] is not None