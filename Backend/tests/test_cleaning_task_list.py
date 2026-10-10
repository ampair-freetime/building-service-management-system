"""Housekeepers see their cleaning tasks as soon as the dashboard loads."""

import asyncio
from uuid import UUID

from conftest import seed_staff
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.dependencies import provide_optional_object_storage
from app.models.enums import ImageType, RequestStatus, RequestType
from app.models.image import Image
from app.models.location import Location
from app.models.service_request import ServiceRequest
from app.services.image_urls import build_image_url

PASSWORD = "Staff-Pass1!"
Context = tuple[TestClient, async_sessionmaker[AsyncSession]]


def _headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"identifier": email, "password": PASSWORD})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _seed(factory, me: UUID, other: UUID) -> dict[str, UUID]:
    """One task per visibility case, plus a repair task that must never appear."""

    async def seed() -> dict[str, UUID]:
        async with factory() as session:
            session.add(Location(id=1, floor="2", area="ห้อง 201"))
            rows = {
                "waiting": (RequestType.CLEANING, RequestStatus.WAITING, None),
                "mine_open": (RequestType.CLEANING, RequestStatus.IN_PROGRESS, me),
                "mine_done": (RequestType.CLEANING, RequestStatus.COMPLETED, me),
                "others": (RequestType.CLEANING, RequestStatus.ASSIGNED, other),
                "repair": (RequestType.REPAIR, RequestStatus.WAITING, None),
            }
            ids = {}
            for index, (key, (request_type, status, assignee)) in enumerate(rows.items()):
                task = ServiceRequest(
                    request_code=f"TASK-{index}",
                    request_type=request_type,
                    location_id=1,
                    title=key,
                    description=f"{key} description",
                    reporter_email="guest@example.com",
                    status=status,
                    assigned_staff_id=assignee,
                )
                session.add(task)
                await session.flush()
                ids[key] = task.id
            await session.commit()
            return ids

    return asyncio.run(seed())


def _setup(test_context: Context):
    client, factory = test_context
    me = seed_staff(factory, email="me@example.com", password=PASSWORD, role="housekeeper")
    other = seed_staff(factory, email="other@example.com", password=PASSWORD, role="housekeeper")
    ids = _seed(factory, me.id, other.id)
    return client, factory, me, ids, _headers(client, "me@example.com")


def test_list_shows_waiting_and_own_tasks_only(test_context: Context) -> None:
    client, _, me, ids, headers = _setup(test_context)

    response = client.get("/api/v1/cleaning-tasks", headers=headers)
    assert response.status_code == 200
    items = {item["title"]: item for item in response.json()["requests"]}
    assert set(items) == {"waiting", "mine_open", "mine_done"}
    assert items["waiting"]["assigned_staff_id"] is None
    assert items["waiting"]["status"] == "waiting"
    assert items["mine_open"]["assigned_staff_id"] == str(me.id)
    assert items["mine_open"]["status"] == "in_progress"
    assert items["waiting"]["location"] == {"id": 1, "floor": "2", "area": "ห้อง 201"}


def test_returned_task_reappears_as_waiting(test_context: Context) -> None:
    client, factory, _, ids, headers = _setup(test_context)
    other_headers = _headers(client, "other@example.com")
    # The other housekeeper returns their task; it must now be visible to me.
    returned = client.post(
        f"/api/v1/cleaning-tasks/{ids['others']}/return",
        headers=other_headers,
        json={"reason": "ไม่สามารถเข้าพื้นที่ได้"},
    )
    assert returned.status_code == 200

    items = {
        item["title"]: item
        for item in client.get("/api/v1/cleaning-tasks", headers=headers).json()["requests"]
    }
    assert items["others"]["status"] == "waiting"
    assert items["others"]["assigned_staff_id"] is None


def test_only_housekeepers_can_list(test_context: Context) -> None:
    client, factory = test_context
    seed_staff(factory, email="tech@example.com", password=PASSWORD, role="technician")
    seed_staff(factory, email="admin@example.com", password=PASSWORD, role="admin")
    for email in ("tech@example.com", "admin@example.com"):
        assert (
            client.get("/api/v1/cleaning-tasks", headers=_headers(client, email)).status_code
            == 403
        )
    assert client.get("/api/v1/cleaning-tasks").status_code == 401


def test_detail_for_visible_task_with_images(test_context: Context) -> None:
    client, factory, _, ids, headers = _setup(test_context)

    async def add_image() -> None:
        async with factory() as session:
            session.add(
                Image(
                    image_type=ImageType.BEFORE,
                    request_id=ids["waiting"],
                    object_key="guest/cleaning/1.webp",
                    bucket_name="test",
                    content_type="image/webp",
                    sort_order=0,
                )
            )
            await session.commit()

    asyncio.run(add_image())

    class Storage:
        def create_download_url(self, key: str) -> str:
            return f"https://example.test/{key}"

    client.app.dependency_overrides[provide_optional_object_storage] = lambda: Storage()
    try:
        response = client.get(f"/api/v1/cleaning-tasks/{ids['waiting']}", headers=headers)
    finally:
        client.app.dependency_overrides.pop(provide_optional_object_storage, None)

    assert response.status_code == 200
    body = response.json()
    assert body["description"] == "waiting description"
    assert body["reporter_email"] == "guest@example.com"
    assert body["location"]["area"] == "ห้อง 201"
    assert [image["url"] for image in body["images"]] == [
        build_image_url(UUID(body["images"][0]["id"]))
    ]


def test_detail_without_storage_still_works(test_context: Context) -> None:
    client, _, _, ids, headers = _setup(test_context)
    client.app.dependency_overrides[provide_optional_object_storage] = lambda: None
    try:
        response = client.get(f"/api/v1/cleaning-tasks/{ids['mine_open']}", headers=headers)
    finally:
        client.app.dependency_overrides.pop(provide_optional_object_storage, None)
    assert response.status_code == 200
    assert response.json()["images"] == []


def test_detail_hides_other_housekeepers_and_repair_tasks(test_context: Context) -> None:
    client, _, _, ids, headers = _setup(test_context)
    for key in ("others", "repair"):
        assert client.get(f"/api/v1/cleaning-tasks/{ids[key]}", headers=headers).status_code == 404
