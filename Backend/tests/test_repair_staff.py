import asyncio
from io import BytesIO

import pytest
from conftest import seed_staff
from fastapi.testclient import TestClient
from PIL import Image as PillowImage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.dependencies import provide_object_storage, provide_optional_object_storage
from app.models.enums import ImageType, RequestAction, RequestStatus, RequestType
from app.models.image import Image
from app.models.location import Location
from app.models.service_request import RequestHistory, ServiceRequest
from app.services.object_storage import StoredObject


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    async def put(self, *, object_key: str, data: bytes, content_type: str) -> StoredObject:
        self.objects[object_key] = (data, content_type)
        return StoredObject(object_key, "test-images", "test-etag")

    async def delete(self, object_key: str) -> None:
        self.objects.pop(object_key, None)

    def create_download_url(self, object_key: str) -> str:
        return f"https://example.test/{object_key}"


@pytest.fixture
def fake_storage(test_context) -> FakeStorage:
    client, _ = test_context
    storage = FakeStorage()

    client.app.dependency_overrides[provide_optional_object_storage] = lambda: storage
    client.app.dependency_overrides[provide_object_storage] = lambda: storage

    yield storage

    client.app.dependency_overrides.pop(
        provide_optional_object_storage,
        None,
    )
    client.app.dependency_overrides.pop(provide_object_storage, None)


def make_png() -> bytes:
    output = BytesIO()
    PillowImage.new("RGB", (32, 24), color="blue").save(output, format="PNG")
    return output.getvalue()


def complete_repair_task(
    client: TestClient,
    request_id,
    headers: dict[str, str],
) -> None:
    assert (
        client.patch(f"/api/v1/repair-requests/{request_id}/accept", headers=headers).status_code
        == 200
    )
    for new_status in ("received", "in_progress"):
        assert (
            client.patch(
                f"/api/v1/repair-requests/{request_id}/status",
                headers=headers,
                json={"status": new_status},
            ).status_code
            == 200
        )
    assert (
        client.patch(f"/api/v1/repair-requests/{request_id}/complete", headers=headers).status_code
        == 200
    )


def seed_location(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def seed() -> None:
        async with session_factory() as session:
            session.add(
                Location(
                    id=1,
                    floor="3",
                    area="ห้อง 301",
                    qr_token="repair-staff-test",
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

    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def seed_service_request(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    request_code: str,
    request_type: RequestType,
    title: str,
) -> None:
    async def seed() -> None:
        async with session_factory() as session:
            session.add(
                ServiceRequest(
                    request_code=request_code,
                    request_type=request_type,
                    location_id=1,
                    title=title,
                    description=f"Description for {title}",
                    reporter_email="guest@example.com",
                )
            )
            await session.commit()

    asyncio.run(seed())


def test_technician_can_view_repair_requests(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="technician1@example.com",
        password="password-one",
        role="technician",
        full_name="Technician One",
    )

    seed_service_request(
        session_factory,
        request_code="REP-001",
        request_type=RequestType.REPAIR,
        title="Air conditioner broken",
    )

    headers = login_staff(client, "TECH001", "password-one")

    response = client.get(
        "/api/v1/repair-requests",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["requests"]) == 1

    request = body["requests"][0]

    assert request["request_code"] == "REP-001"
    assert request["title"] == "Air conditioner broken"
    assert request["description"] == "Description for Air conditioner broken"
    assert request["priority"] == "normal"
    assert request["status"] == "waiting"
    assert request["location"]["id"] == 1
    assert request["location"]["floor"] == "3"
    assert request["location"]["area"] == "ห้อง 301"
    assert request["assigned_staff_id"] is None
    assert request["created_at"] is not None


def test_repair_list_does_not_include_cleaning_requests(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="technician1@example.com",
        password="password-one",
        role="technician",
        full_name="Technician One",
    )

    seed_service_request(
        session_factory,
        request_code="REP-001",
        request_type=RequestType.REPAIR,
        title="Broken light",
    )

    seed_service_request(
        session_factory,
        request_code="CLN-001",
        request_type=RequestType.CLEANING,
        title="Dirty floor",
    )

    headers = login_staff(client, "TECH001", "password-one")

    response = client.get(
        "/api/v1/repair-requests",
        headers=headers,
    )

    assert response.status_code == 200

    requests = response.json()["requests"]

    assert len(requests) == 1
    assert requests[0]["request_code"] == "REP-001"


def test_repair_list_is_empty_when_no_repair_requests(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="technician1@example.com",
        password="password-one",
        role="technician",
        full_name="Technician One",
    )

    headers = login_staff(client, "TECH001", "password-one")

    response = client.get(
        "/api/v1/repair-requests",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {"requests": []}


def test_non_technician_cannot_view_repair_requests(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_staff(
        session_factory,
        staff_code="HK001",
        email="housekeeper@example.com",
        password="password-one",
        role="housekeeper",
        full_name="Housekeeper One",
    )

    headers = login_staff(client, "HK001", "password-one")

    response = client.get(
        "/api/v1/repair-requests",
        headers=headers,
    )

    assert response.status_code == 403


def test_technician_can_view_repair_request_detail(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="technician1@example.com",
        password="password-one",
        role="technician",
        full_name="Technician One",
    )

    seed_service_request(
        session_factory,
        request_code="REP-DETAIL-001",
        request_type=RequestType.REPAIR,
        title="Broken air conditioner",
    )

    headers = login_staff(client, "TECH001", "password-one")

    response = client.get(
        "/api/v1/repair-requests",
        headers=headers,
    )
    request_id = response.json()["requests"][0]["id"]

    response = client.get(
        f"/api/v1/repair-requests/{request_id}",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == request_id
    assert body["request_code"] == "REP-DETAIL-001"
    assert body["title"] == "Broken air conditioner"
    assert body["description"] == "Description for Broken air conditioner"
    assert body["priority"] == "normal"
    assert body["status"] == "waiting"
    assert body["reporter_email"] == "guest@example.com"

    assert body["location"]["id"] == 1
    assert body["location"]["floor"] == "3"
    assert body["location"]["area"] == "ห้อง 301"

    assert body["assigned_staff_id"] is None
    assert body["images"] == []
    assert body["created_at"] is not None
    assert body["updated_at"] is not None
    assert body["completed_at"] is None


def test_repair_detail_returns_404_when_request_not_found(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    from uuid import uuid4

    client, session_factory = test_context

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="technician1@example.com",
        password="password-one",
        role="technician",
        full_name="Technician One",
    )

    headers = login_staff(client, "TECH001", "password-one")

    response = client.get(
        f"/api/v1/repair-requests/{uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Repair request not found"


def test_repair_detail_does_not_allow_cleaning_request(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="technician1@example.com",
        password="password-one",
        role="technician",
        full_name="Technician One",
    )

    seed_service_request(
        session_factory,
        request_code="CLN-DETAIL-001",
        request_type=RequestType.CLEANING,
        title="Dirty floor",
    )

    headers = login_staff(client, "TECH001", "password-one")

    async def get_cleaning_request_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(ServiceRequest.request_code == "CLN-DETAIL-001")
            )
            assert request is not None
            return request.id

    request_id = asyncio.run(get_cleaning_request_id())

    response = client.get(
        f"/api/v1/repair-requests/{request_id}",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Repair request not found"


def test_repair_detail_includes_attached_images(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeStorage,
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="technician1@example.com",
        password="password-one",
        role="technician",
        full_name="Technician One",
    )

    seed_service_request(
        session_factory,
        request_code="REP-IMAGE-001",
        request_type=RequestType.REPAIR,
        title="Broken air conditioner",
    )

    async def seed_images():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(ServiceRequest.request_code == "REP-IMAGE-001")
            )
            assert request is not None

            session.add_all(
                [
                    Image(
                        request_id=request.id,
                        object_key="repair/test/second.webp",
                        image_type=ImageType.BEFORE,
                        content_type="image/webp",
                        size_bytes=200,
                        width=800,
                        height=600,
                        sort_order=1,
                    ),
                    Image(
                        request_id=request.id,
                        object_key="repair/test/first.webp",
                        image_type=ImageType.BEFORE,
                        content_type="image/webp",
                        size_bytes=100,
                        width=640,
                        height=480,
                        sort_order=0,
                    ),
                ]
            )

            await session.commit()

            return request.id

    request_id = asyncio.run(seed_images())

    headers = login_staff(
        client,
        "TECH001",
        "password-one",
    )

    response = client.get(
        f"/api/v1/repair-requests/{request_id}",
        headers=headers,
    )

    assert response.status_code == 200

    images = response.json()["images"]

    assert len(images) == 2

    assert images[0]["image_type"] == "before"
    assert images[0]["sort_order"] == 0
    assert images[0]["url"] == ("https://example.test/repair/test/first.webp")
    assert images[0]["content_type"] == "image/webp"
    assert images[0]["size_bytes"] == 100
    assert images[0]["width"] == 640
    assert images[0]["height"] == 480

    assert images[1]["sort_order"] == 1
    assert images[1]["url"] == ("https://example.test/repair/test/second.webp")


def test_technician_can_accept_repair_task(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="technician1@example.com",
        password="password-one",
        role="technician",
        full_name="Technician One",
    )

    seed_service_request(
        session_factory,
        request_code="REP-ACCEPT-001",
        request_type=RequestType.REPAIR,
        title="Air conditioner broken",
    )

    headers = login_staff(client, "TECH001", "password-one")

    async def get_request_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(ServiceRequest.request_code == "REP-ACCEPT-001")
            )
            assert request is not None
            return request.id

    request_id = asyncio.run(get_request_id())

    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/accept",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == str(request_id)
    assert body["request_code"] == "REP-ACCEPT-001"
    assert body["status"] == "assigned"
    assert body["assigned_staff"]["staff_code"] == "TECH001"
    assert body["assigned_staff"]["full_name"] == "Technician One"

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


def test_second_technician_cannot_accept_assigned_repair_task(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="technician1@example.com",
        password="password-one",
        role="technician",
        full_name="Technician One",
    )

    seed_staff(
        session_factory,
        staff_code="TECH002",
        email="technician2@example.com",
        password="password-two",
        role="technician",
        full_name="Technician Two",
    )

    seed_service_request(
        session_factory,
        request_code="REP-ACCEPT-002",
        request_type=RequestType.REPAIR,
        title="Broken light",
    )

    tech1_headers = login_staff(
        client,
        "TECH001",
        "password-one",
    )

    tech2_headers = login_staff(
        client,
        "TECH002",
        "password-two",
    )

    async def get_request_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(ServiceRequest.request_code == "REP-ACCEPT-002")
            )
            assert request is not None
            return request.id

    request_id = asyncio.run(get_request_id())

    # TECH001 รับงานก่อน
    first = client.patch(
        f"/api/v1/repair-requests/{request_id}/accept",
        headers=tech1_headers,
    )

    assert first.status_code == 200
    assert first.json()["assigned_staff"]["staff_code"] == "TECH001"

    # TECH002 พยายามรับงานเดียวกัน
    second = client.patch(
        f"/api/v1/repair-requests/{request_id}/accept",
        headers=tech2_headers,
    )

    assert second.status_code == 409
    assert second.json()["detail"] == ("Repair task has already been assigned")

    # งานต้องยังเป็นของ TECH001 และมี ACCEPTED history แค่ครั้งเดียว
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
            assert histories[0].target_staff_id == task.assigned_staff_id

    asyncio.run(verify_database())


def test_technician_can_update_repair_status_to_received(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="technician1@example.com",
        password="password-one",
        role="technician",
        full_name="Technician One",
    )

    seed_service_request(
        session_factory,
        request_code="REP-STATUS-001",
        request_type=RequestType.REPAIR,
        title="Broken air conditioner",
    )

    headers = login_staff(client, "TECH001", "password-one")

    async def get_request_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(ServiceRequest.request_code == "REP-STATUS-001")
            )
            assert request is not None
            return request.id

    request_id = asyncio.run(get_request_id())

    # รับงานก่อน: WAITING → ASSIGNED
    accepted = client.patch(
        f"/api/v1/repair-requests/{request_id}/accept",
        headers=headers,
    )
    assert accepted.status_code == 200

    # เปลี่ยนสถานะ: ASSIGNED → RECEIVED
    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/status",
        headers=headers,
        json={"status": "received"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "received"

    async def verify_database() -> None:
        async with session_factory() as session:
            task = await session.get(ServiceRequest, request_id)

            assert task is not None
            assert task.status == RequestStatus.RECEIVED

            history = await session.scalar(
                select(RequestHistory).where(
                    RequestHistory.request_id == request_id,
                    RequestHistory.action == RequestAction.STATUS_CHANGED,
                    RequestHistory.new_status == RequestStatus.RECEIVED,
                )
            )

            assert history is not None
            assert history.old_status == RequestStatus.ASSIGNED
            assert history.new_status == RequestStatus.RECEIVED

    asyncio.run(verify_database())


def test_technician_can_update_repair_status_to_in_progress(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="technician1@example.com",
        password="password-one",
        role="technician",
        full_name="Technician One",
    )

    seed_service_request(
        session_factory,
        request_code="REP-STATUS-002",
        request_type=RequestType.REPAIR,
        title="Broken light",
    )

    headers = login_staff(client, "TECH001", "password-one")

    async def get_request_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(ServiceRequest.request_code == "REP-STATUS-002")
            )
            assert request is not None
            return request.id

    request_id = asyncio.run(get_request_id())

    # WAITING → ASSIGNED
    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/accept",
        headers=headers,
    )
    assert response.status_code == 200

    # ASSIGNED → RECEIVED
    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/status",
        headers=headers,
        json={"status": "received"},
    )
    assert response.status_code == 200

    # RECEIVED → IN_PROGRESS
    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/status",
        headers=headers,
        json={"status": "in_progress"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"

    async def verify_database() -> None:
        async with session_factory() as session:
            task = await session.get(ServiceRequest, request_id)

            assert task is not None
            assert task.status == RequestStatus.IN_PROGRESS

            history = await session.scalar(
                select(RequestHistory).where(
                    RequestHistory.request_id == request_id,
                    RequestHistory.action == RequestAction.STATUS_CHANGED,
                    RequestHistory.new_status == RequestStatus.IN_PROGRESS,
                )
            )

            assert history is not None
            assert history.old_status == RequestStatus.RECEIVED
            assert history.new_status == RequestStatus.IN_PROGRESS

    asyncio.run(verify_database())


def test_technician_cannot_skip_repair_status(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="technician1@example.com",
        password="password-one",
        role="technician",
        full_name="Technician One",
    )

    seed_service_request(
        session_factory,
        request_code="REP-STATUS-003",
        request_type=RequestType.REPAIR,
        title="Broken door",
    )

    headers = login_staff(client, "TECH001", "password-one")

    async def get_request_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(ServiceRequest.request_code == "REP-STATUS-003")
            )
            assert request is not None
            return request.id

    request_id = asyncio.run(get_request_id())

    # WAITING → ASSIGNED
    accepted = client.patch(
        f"/api/v1/repair-requests/{request_id}/accept",
        headers=headers,
    )
    assert accepted.status_code == 200

    # พยายามข้าม ASSIGNED → IN_PROGRESS
    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/status",
        headers=headers,
        json={"status": "in_progress"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Cannot change repair task status from assigned to in_progress"
    )

    # สถานะใน DB ต้องยังเป็น ASSIGNED
    async def verify_database() -> None:
        async with session_factory() as session:
            task = await session.get(ServiceRequest, request_id)

            assert task is not None
            assert task.status == RequestStatus.ASSIGNED

    asyncio.run(verify_database())


def test_other_technician_cannot_update_repair_status(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="technician1@example.com",
        password="password-one",
        role="technician",
        full_name="Technician One",
    )

    seed_staff(
        session_factory,
        staff_code="TECH002",
        email="technician2@example.com",
        password="password-two",
        role="technician",
        full_name="Technician Two",
    )

    seed_service_request(
        session_factory,
        request_code="REP-STATUS-004",
        request_type=RequestType.REPAIR,
        title="Broken fan",
    )

    tech1_headers = login_staff(client, "TECH001", "password-one")
    tech2_headers = login_staff(client, "TECH002", "password-two")

    async def get_request_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(ServiceRequest.request_code == "REP-STATUS-004")
            )
            assert request is not None
            return request.id

    request_id = asyncio.run(get_request_id())

    # TECH001 รับงาน
    accepted = client.patch(
        f"/api/v1/repair-requests/{request_id}/accept",
        headers=tech1_headers,
    )
    assert accepted.status_code == 200

    # TECH002 พยายามเปลี่ยนสถานะงานของ TECH001
    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/status",
        headers=tech2_headers,
        json={"status": "received"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == ("Repair task is assigned to another technician")

    async def verify_database() -> None:
        async with session_factory() as session:
            task = await session.get(ServiceRequest, request_id)

            assert task is not None
            assert task.status == RequestStatus.ASSIGNED

    asyncio.run(verify_database())


def test_technician_can_complete_repair_task(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="complete-repair@example.com",
        password="correct-password",
        role="technician",
        full_name="Technician One",
    )

    seed_service_request(
        session_factory,
        request_code="REP-COMPLETE-001",
        request_type=RequestType.REPAIR,
        title="Broken air conditioner",
    )

    headers = login_staff(
        client,
        "TECH001",
        "correct-password",
    )

    async def get_request_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(ServiceRequest.request_code == "REP-COMPLETE-001")
            )
            assert request is not None
            return request.id

    request_id = asyncio.run(get_request_id())

    # WAITING → ASSIGNED
    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/accept",
        headers=headers,
    )
    assert response.status_code == 200

    # ASSIGNED → RECEIVED
    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/status",
        headers=headers,
        json={"status": "received"},
    )
    assert response.status_code == 200

    # RECEIVED → IN_PROGRESS
    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/status",
        headers=headers,
        json={"status": "in_progress"},
    )
    assert response.status_code == 200

    # IN_PROGRESS → COMPLETED
    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/complete",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    async def verify_database() -> None:
        async with session_factory() as session:
            task = await session.get(ServiceRequest, request_id)

            assert task is not None
            assert task.status == RequestStatus.COMPLETED
            assert task.completed_at is not None

            history = await session.scalar(
                select(RequestHistory).where(
                    RequestHistory.request_id == request_id,
                    RequestHistory.action == RequestAction.COMPLETED,
                )
            )

            assert history is not None
            assert history.old_status == RequestStatus.IN_PROGRESS
            assert history.new_status == RequestStatus.COMPLETED

    asyncio.run(verify_database())


def test_technician_cannot_complete_repair_before_in_progress(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="early-complete@example.com",
        password="correct-password",
        role="technician",
        full_name="Technician One",
    )

    seed_service_request(
        session_factory,
        request_code="REP-COMPLETE-002",
        request_type=RequestType.REPAIR,
        title="Broken light",
    )

    headers = login_staff(
        client,
        "TECH001",
        "correct-password",
    )

    async def get_request_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(ServiceRequest.request_code == "REP-COMPLETE-002")
            )
            assert request is not None
            return request.id

    request_id = asyncio.run(get_request_id())

    # WAITING → ASSIGNED เท่านั้น
    accepted = client.patch(
        f"/api/v1/repair-requests/{request_id}/accept",
        headers=headers,
    )
    assert accepted.status_code == 200

    # พยายาม Complete ทั้งที่ยัง ASSIGNED
    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/complete",
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == ("Repair task must be in progress before completion")

    async def verify_database() -> None:
        async with session_factory() as session:
            task = await session.get(ServiceRequest, request_id)

            assert task is not None
            assert task.status == RequestStatus.ASSIGNED
            assert task.completed_at is None

    asyncio.run(verify_database())


def test_other_technician_cannot_complete_repair_task(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="owner-complete@example.com",
        password="correct-password",
        role="technician",
        full_name="Technician One",
    )

    seed_staff(
        session_factory,
        staff_code="TECH002",
        email="other-complete@example.com",
        password="correct-password",
        role="technician",
        full_name="Technician Two",
    )

    seed_service_request(
        session_factory,
        request_code="REP-COMPLETE-003",
        request_type=RequestType.REPAIR,
        title="Broken fan",
    )

    tech1_headers = login_staff(
        client,
        "TECH001",
        "correct-password",
    )

    tech2_headers = login_staff(
        client,
        "TECH002",
        "correct-password",
    )

    async def get_request_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(ServiceRequest.request_code == "REP-COMPLETE-003")
            )
            assert request is not None
            return request.id

    request_id = asyncio.run(get_request_id())

    # TECH001 ทำงานจนถึง IN_PROGRESS
    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/accept",
        headers=tech1_headers,
    )
    assert response.status_code == 200

    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/status",
        headers=tech1_headers,
        json={"status": "received"},
    )
    assert response.status_code == 200

    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/status",
        headers=tech1_headers,
        json={"status": "in_progress"},
    )
    assert response.status_code == 200

    # TECH002 พยายาม Complete งานของ TECH001
    response = client.patch(
        f"/api/v1/repair-requests/{request_id}/complete",
        headers=tech2_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == ("Repair task is assigned to another technician")

    async def verify_database() -> None:
        async with session_factory() as session:
            task = await session.get(ServiceRequest, request_id)

            assert task is not None
            assert task.status == RequestStatus.IN_PROGRESS
            assert task.completed_at is None

    asyncio.run(verify_database())


def test_technician_can_add_repair_completion_note(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="repair-note@example.com",
        password="correct-password",
        role="technician",
        full_name="Technician One",
    )

    seed_service_request(
        session_factory,
        request_code="REP-NOTE-001",
        request_type=RequestType.REPAIR,
        title="Broken air conditioner",
    )

    headers = login_staff(
        client,
        "TECH001",
        "correct-password",
    )

    async def get_request_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(ServiceRequest.request_code == "REP-NOTE-001")
            )
            assert request is not None
            return request.id

    request_id = asyncio.run(get_request_id())

    # ทำงานจน COMPLETED
    assert (
        client.patch(
            f"/api/v1/repair-requests/{request_id}/accept",
            headers=headers,
        ).status_code
        == 200
    )

    assert (
        client.patch(
            f"/api/v1/repair-requests/{request_id}/status",
            headers=headers,
            json={"status": "received"},
        ).status_code
        == 200
    )

    assert (
        client.patch(
            f"/api/v1/repair-requests/{request_id}/status",
            headers=headers,
            json={"status": "in_progress"},
        ).status_code
        == 200
    )

    assert (
        client.patch(
            f"/api/v1/repair-requests/{request_id}/complete",
            headers=headers,
        ).status_code
        == 200
    )

    # เพิ่ม Repair Note
    response = client.post(
        f"/api/v1/repair-requests/{request_id}/completion-note",
        headers=headers,
        json={"note": "Replaced damaged air conditioner component"},
    )

    assert response.status_code == 200
    assert response.json()["request_id"] == str(request_id)
    assert response.json()["note"] == ("Replaced damaged air conditioner component")

    async def verify_history() -> None:
        async with session_factory() as session:
            history = await session.scalar(
                select(RequestHistory).where(
                    RequestHistory.request_id == request_id,
                    RequestHistory.action == RequestAction.COMPLETION_NOTE_ADDED,
                )
            )

            assert history is not None
            assert history.note == ("Replaced damaged air conditioner component")
            assert history.old_status == RequestStatus.COMPLETED
            assert history.new_status == RequestStatus.COMPLETED

    asyncio.run(verify_history())


def test_technician_cannot_add_repair_note_before_completed(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="early-note@example.com",
        password="correct-password",
        role="technician",
        full_name="Technician One",
    )

    seed_service_request(
        session_factory,
        request_code="REP-NOTE-002",
        request_type=RequestType.REPAIR,
        title="Broken light",
    )

    headers = login_staff(
        client,
        "TECH001",
        "correct-password",
    )

    async def get_request_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(ServiceRequest.request_code == "REP-NOTE-002")
            )
            assert request is not None
            return request.id

    request_id = asyncio.run(get_request_id())

    # รับงาน แต่ยังไม่ทำจน COMPLETED
    assert (
        client.patch(
            f"/api/v1/repair-requests/{request_id}/accept",
            headers=headers,
        ).status_code
        == 200
    )

    # พยายามเพิ่ม note ตอนสถานะยัง ASSIGNED
    response = client.post(
        f"/api/v1/repair-requests/{request_id}/completion-note",
        headers=headers,
        json={"note": "Trying to add note too early"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == ("Repair task must be completed before adding a note")

    async def verify_history() -> None:
        async with session_factory() as session:
            history = await session.scalar(
                select(RequestHistory).where(
                    RequestHistory.request_id == request_id,
                    RequestHistory.action == RequestAction.COMPLETION_NOTE_ADDED,
                )
            )

            assert history is None

    asyncio.run(verify_history())


def test_repair_completion_note_appears_in_work_history(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="repair-history@example.com",
        password="correct-password",
        role="technician",
        full_name="Technician One",
    )

    seed_service_request(
        session_factory,
        request_code="REP-HISTORY-001",
        request_type=RequestType.REPAIR,
        title="Broken air conditioner",
    )

    headers = login_staff(
        client,
        "TECH001",
        "correct-password",
    )

    async def get_request_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(ServiceRequest.request_code == "REP-HISTORY-001")
            )
            assert request is not None
            return request.id

    request_id = asyncio.run(get_request_id())

    # ทำงานจน COMPLETED
    assert (
        client.patch(
            f"/api/v1/repair-requests/{request_id}/accept",
            headers=headers,
        ).status_code
        == 200
    )

    assert (
        client.patch(
            f"/api/v1/repair-requests/{request_id}/status",
            headers=headers,
            json={"status": "received"},
        ).status_code
        == 200
    )

    assert (
        client.patch(
            f"/api/v1/repair-requests/{request_id}/status",
            headers=headers,
            json={"status": "in_progress"},
        ).status_code
        == 200
    )

    assert (
        client.patch(
            f"/api/v1/repair-requests/{request_id}/complete",
            headers=headers,
        ).status_code
        == 200
    )

    # เพิ่ม Repair Note
    assert (
        client.post(
            f"/api/v1/repair-requests/{request_id}/completion-note",
            headers=headers,
            json={"note": "Replaced damaged component"},
        ).status_code
        == 200
    )

    # ดู Work History
    response = client.get(
        f"/api/v1/repair-requests/{request_id}/history",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["request_id"] == str(request_id)

    completion_notes = [
        item for item in data["history"] if item["action"] == "completion_note_added"
    ]

    assert len(completion_notes) == 1
    assert completion_notes[0]["note"] == "Replaced damaged component"
    assert completion_notes[0]["old_status"] == "completed"
    assert completion_notes[0]["new_status"] == "completed"


def test_technician_can_upload_repair_completion_photos(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
    fake_storage: FakeStorage,
) -> None:
    client, session_factory = test_context
    seed_location(session_factory)
    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="repair-photo@example.com",
        password="correct-password",
        role="technician",
        full_name="Technician One",
    )
    seed_service_request(
        session_factory,
        request_code="REP-PHOTO-001",
        request_type=RequestType.REPAIR,
        title="Broken projector",
    )
    headers = login_staff(client, "TECH001", "correct-password")

    async def get_request_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(ServiceRequest.request_code == "REP-PHOTO-001")
            )
            assert request is not None
            return request.id

    request_id = asyncio.run(get_request_id())
    complete_repair_task(client, request_id, headers)
    response = client.post(
        f"/api/v1/repair-requests/{request_id}/completion-photos",
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
    assert all(photo["content_type"] == "image/webp" for photo in body["photos"])
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
            assert all(image.uploaded_by_staff_id is not None for image in images)
            assert all(image.width == 32 and image.height == 24 for image in images)

    asyncio.run(verify_database())
