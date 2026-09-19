import asyncio
from io import BytesIO

import pytest
from PIL import Image as PillowImage
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.dependencies import provide_optional_object_storage
from app.models.image import Image
from app.models.location import Location
from app.models.service_request import RequestHistory, ServiceRequest
from app.services.object_storage import StorageOperationError, StoredObject


class FakeStorage:
    """R2 ตัวปลอมสำหรับทดสอบ API โดยไม่เรียก network."""

    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.fail_put = False

    async def put(self, *, object_key: str, data: bytes, content_type: str) -> StoredObject:
        if self.fail_put:
            raise StorageOperationError("simulated R2 failure")
        self.objects[object_key] = (data, content_type)
        return StoredObject(object_key=object_key, bucket_name="test-images", etag="etag")

    async def delete(self, object_key: str) -> None:
        self.objects.pop(object_key, None)


@pytest.fixture
def fake_storage(test_context) -> FakeStorage:
    client, _ = test_context
    storage = FakeStorage()
    client.app.dependency_overrides[provide_optional_object_storage] = lambda: storage
    yield storage
    client.app.dependency_overrides.pop(provide_optional_object_storage, None)


def make_png() -> bytes:
    output = BytesIO()
    PillowImage.new("RGB", (32, 24), color="blue").save(output, format="PNG")
    return output.getvalue()


def cleaning_form(**changes) -> dict[str, str]:
    values = {
        "title": "พื้นเปียก",
        "description": "ข้างลิฟต์ตัวซ้าย",
        "priority": "urgent",
        "reporter_email": "GUEST@EXAMPLE.COM",
        "location_id": "1",
    }
    values.update(changes)
    return values


def seed_locations(factory: async_sessionmaker[AsyncSession]) -> None:
    async def seed() -> None:
        async with factory() as session:
            session.add_all(
                [
                    Location(
                        id=1,
                        floor="2",
                        area="ห้อง 201",
                        qr_token="active",
                    ),
                    Location(id=2, area="ห้องน้ำ", qr_token="inactive", is_active=False),
                    Location(id=3, floor="1", area="โถง", qr_token="first"),
                ]
            )
            await session.commit()

    asyncio.run(seed())


def row_counts(factory: async_sessionmaker[AsyncSession]) -> tuple[int, int, int]:
    async def read() -> tuple[int, int, int]:
        async with factory() as session:
            counts = []
            for model in (ServiceRequest, RequestHistory, Image):
                counts.append(await session.scalar(select(func.count()).select_from(model)))
            return tuple(counts)

    return asyncio.run(read())


def test_locations_and_qr_routes_are_not_captured_as_request_codes(test_context) -> None:
    client, factory = test_context
    seed_locations(factory)

    response = client.get("/api/v1/guest/cleaning-requests/locations")
    assert response.status_code == 200
    assert [location["id"] for location in response.json()] == [3, 1]

    resolved = client.get("/api/v1/guest/cleaning-requests/locations/by-qr/active")
    assert resolved.status_code == 200
    assert resolved.json()["id"] == 1
    assert client.get("/api/v1/guest/cleaning-requests/locations/by-qr/inactive").status_code == 404
    assert client.get("/api/v1/guest/cleaning-requests/locations/by-qr/missing").status_code == 404


def test_qr_flow_create_and_track(test_context, fake_storage) -> None:
    client, factory = test_context
    seed_locations(factory)

    qr = client.get("/api/v1/guest/cleaning-requests/locations/by-qr/%20active%20")
    assert qr.status_code == 200
    location_id = qr.json()["id"]

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data=cleaning_form(location_id=str(location_id)),
    )
    assert created.status_code == 201
    body = created.json()
    assert body["request_code"].startswith("CLN-")
    assert body["location"] == "ชั้น 2 ห้อง 201"
    assert body["image_count"] == 0

    tracked = client.get(
        f"/api/v1/guest/cleaning-requests/{body['request_code'].lower()}",
        params={"reporter_email": "guest@EXAMPLE.com"},
    )
    assert tracked.status_code == 200
    assert tracked.json()["status"] == "waiting"
    assert "request_code" not in tracked.json()

    for code, email in (
        (body["request_code"], "other@example.com"),
        ("CLN-MISSING", "guest@example.com"),
    ):
        response = client.get(
            f"/api/v1/guest/cleaning-requests/{code}",
            params={"reporter_email": email},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "ไม่พบคำร้องนี้"
    assert client.get(f"/api/v1/guest/cleaning-requests/{body['request_code']}").status_code == 422


def test_inactive_location_between_qr_and_post_is_rejected(test_context, fake_storage) -> None:
    client, factory = test_context
    seed_locations(factory)
    assert client.get("/api/v1/guest/cleaning-requests/locations/by-qr/active").status_code == 200

    async def deactivate() -> None:
        async with factory() as session:
            location = await session.get(Location, 1)
            location.is_active = False
            await session.commit()

    asyncio.run(deactivate())
    response = client.post("/api/v1/guest/cleaning-requests", data=cleaning_form())
    assert response.status_code == 422
    assert row_counts(factory) == (0, 0, 0)


def test_post_without_image_works_without_r2_configuration(test_context) -> None:
    client, factory = test_context
    seed_locations(factory)
    client.app.dependency_overrides[provide_optional_object_storage] = lambda: None

    response = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ขยะเต็มถัง",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )
    assert response.status_code == 201
    assert response.json()["image_count"] == 0
    assert row_counts(factory) == (1, 1, 0)


def test_one_image_is_normalized_and_saved(test_context, fake_storage) -> None:
    client, factory = test_context
    seed_locations(factory)
    response = client.post(
        "/api/v1/guest/cleaning-requests",
        data=cleaning_form(),
        files={"image": ("floor.png", make_png(), "image/png")},
    )
    assert response.status_code == 201
    assert response.json()["image_count"] == 1
    assert len(fake_storage.objects) == 1
    object_key, (data, content_type) = next(iter(fake_storage.objects.items()))
    assert object_key.startswith("cleaning/") and object_key.endswith(".webp")
    assert content_type == "image/webp"
    assert data.startswith(b"RIFF")
    assert row_counts(factory) == (1, 1, 1)


def test_image_requires_configured_storage(test_context) -> None:
    client, factory = test_context
    seed_locations(factory)
    client.app.dependency_overrides[provide_optional_object_storage] = lambda: None
    response = client.post(
        "/api/v1/guest/cleaning-requests",
        data=cleaning_form(),
        files={"image": ("floor.png", make_png(), "image/png")},
    )
    assert response.status_code == 503
    assert row_counts(factory) == (0, 0, 0)


@pytest.mark.parametrize(
    ("data", "files"),
    [
        ({"reporter_email": "guest@example.com", "location_id": "1"}, None),
        (cleaning_form(priority="high"), None),
        (cleaning_form(qr_token="must-not-be-posted"), None),
        (cleaning_form(), {"image": ("fake.png", b"not-an-image", "image/png")}),
    ],
)
def test_invalid_form_or_image_returns_422(test_context, fake_storage, data, files) -> None:
    client, factory = test_context
    seed_locations(factory)
    response = client.post("/api/v1/guest/cleaning-requests", data=data, files=files)
    assert response.status_code == 422
    assert row_counts(factory) == (0, 0, 0)


def test_storage_failure_returns_502_and_rolls_back(test_context, fake_storage) -> None:
    client, factory = test_context
    seed_locations(factory)
    fake_storage.fail_put = True
    response = client.post(
        "/api/v1/guest/cleaning-requests",
        data=cleaning_form(),
        files={"image": ("floor.png", make_png(), "image/png")},
    )
    assert response.status_code == 502
    assert row_counts(factory) == (0, 0, 0)


def test_five_images_and_empty_field_are_saved_in_order(test_context, fake_storage) -> None:
    client, factory = test_context
    seed_locations(factory)
    files = [
        ("image", (f"floor-{index}.png", make_png(), "image/png"))
        for index in range(5)
    ]
    files.append(("image", ("", b"", "application/octet-stream")))

    response = client.post(
        "/api/v1/guest/cleaning-requests",
        data=cleaning_form(),
        files=files,
    )

    assert response.status_code == 201
    assert response.json()["image_count"] == 5
    assert len(fake_storage.objects) == 5
    assert row_counts(factory) == (1, 1, 5)

    async def read_sort_orders() -> list[int | None]:
        async with factory() as session:
            return list(
                await session.scalars(select(Image.sort_order).order_by(Image.sort_order))
            )

    assert asyncio.run(read_sort_orders()) == [0, 1, 2, 3, 4]


def test_six_images_are_rejected_before_storage(test_context, fake_storage) -> None:
    client, factory = test_context
    seed_locations(factory)
    response = client.post(
        "/api/v1/guest/cleaning-requests",
        data=cleaning_form(),
        files=[
            ("image", (f"floor-{index}.png", make_png(), "image/png"))
            for index in range(6)
        ],
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "image"]
    assert not fake_storage.objects
    assert row_counts(factory) == (0, 0, 0)


def test_invalid_third_image_removes_previous_objects(test_context, fake_storage) -> None:
    client, factory = test_context
    seed_locations(factory)
    response = client.post(
        "/api/v1/guest/cleaning-requests",
        data=cleaning_form(),
        files=[
            ("image", ("first.png", make_png(), "image/png")),
            ("image", ("second.png", make_png(), "image/png")),
            ("image", ("invalid.png", b"not-an-image", "image/png")),
        ],
    )

    assert response.status_code == 422
    assert not fake_storage.objects
    assert row_counts(factory) == (0, 0, 0)
