import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import seed_staff

from app.api.dependencies import provide_optional_object_storage
from app.models.enums import ImageType, RequestType
from app.models.image import Image
from app.models.location import Location
from app.models.service_request import ServiceRequest


class FakeStorage:
    def create_download_url(self, object_key: str) -> str:
        return f"https://example.test/{object_key}"


@pytest.fixture
def fake_storage(test_context) -> FakeStorage:
    client, _ = test_context
    storage = FakeStorage()

    client.app.dependency_overrides[
        provide_optional_object_storage
    ] = lambda: storage

    yield storage

    client.app.dependency_overrides.pop(
        provide_optional_object_storage,
        None,
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

    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }


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
                select(ServiceRequest).where(
                    ServiceRequest.request_code == "CLN-DETAIL-001"
                )
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
                select(ServiceRequest).where(
                    ServiceRequest.request_code == "REP-IMAGE-001"
                )
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
    assert images[0]["url"] == (
        "https://example.test/repair/test/first.webp"
    )
    assert images[0]["content_type"] == "image/webp"
    assert images[0]["size_bytes"] == 100
    assert images[0]["width"] == 640
    assert images[0]["height"] == 480

    assert images[1]["sort_order"] == 1
    assert images[1]["url"] == (
        "https://example.test/repair/test/second.webp"
    )