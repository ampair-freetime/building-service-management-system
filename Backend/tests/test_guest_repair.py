import asyncio
from io import BytesIO
from unittest.mock import AsyncMock

import pytest
from fastapi import UploadFile
from PIL import Image as PillowImage
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.datastructures import Headers

from app.models.enums import ImageType, RequestAction, RequestStatus, RequestType
from app.models.image import Image
from app.models.location import Location
from app.models.service_request import RequestHistory, ServiceRequest
from app.schemas.repair_guest import GuestRepairCreate
from app.services import repair_guest
from app.services.images import InvalidImageError
from app.services.object_storage import StorageOperationError, StoredObject
from app.services.repair_guest import (
    RepairLocationNotFoundError,
    RepairRequestNotFoundError,
    RepairRequestPersistenceError,
    create_guest_repair_request,
    get_guest_repair_status,
    list_guest_repair_locations,
    resolve_guest_repair_location_by_qr,
)


class FakeStorage:
    """เก็บรูปในหน่วยความจำเพื่อทดสอบ commit/rollback โดยไม่เรียก R2."""

    def __init__(self):
        self.objects = {}
        self.deleted = []

    async def put(self, *, object_key, data, content_type):
        self.objects[object_key] = (data, content_type)
        return StoredObject(object_key=object_key, bucket_name="test", etag="test-etag")

    async def delete(self, object_key):
        self.deleted.append(object_key)
        self.objects.pop(object_key, None)


def image_upload():
    data = BytesIO()
    PillowImage.new("RGB", (32, 24), color="blue").save(data, format="PNG")
    data.seek(0)
    return UploadFile(
        file=data, filename="repair.png", headers=Headers({"content-type": "image/png"})
    )


async def seed_location(factory):
    async with factory() as session:
        session.add(Location(id=1, area="ห้อง 101", qr_token="active"))
        await session.commit()


async def assert_no_requests(factory):
    # อ่านจาก session ใหม่ เพื่อยืนยันว่าไม่มีข้อมูลหลุด commit ลงฐานข้อมูล
    async with factory() as session:
        for model in (ServiceRequest, RequestHistory, Image):
            assert await session.scalar(select(func.count()).select_from(model)) == 0


def payload(**changes):
    data = {
        "title": "พื้นเปียก",
        "description": "ข้างลิฟต์ตัวซ้าย",
        "priority": "normal",
        "reporter_email": "Guest@EXAMPLE.COM",
        "location_id": 1,
    }
    data.update(changes)
    return GuestRepairCreate(**data)


@pytest.mark.parametrize(
    "changes",
    [
        {"location_id": None},
        {"location_id": 0},
        {"location_detail": "old free text"},
        {"category_id": 1},
        {"request_type": "cleaning"},
        {"title": "   "},
        {"description": "x" * 1001},
        {"priority": "high"},
    ],
)
def test_rejects_invalid_location_and_client_controlled_type(changes):
    with pytest.raises(ValidationError):
        payload(**changes)


def test_location_is_required():
    data = payload().model_dump()
    del data["location_id"]
    with pytest.raises(ValidationError):
        GuestRepairCreate(**data)


def test_create_list_qr_and_tracking(test_context):
    _, factory = test_context

    async def run():
        async with factory() as session:
            session.add_all(
                [
                    Location(id=1, floor="2", area="ห้อง 201", qr_token="active"),
                    Location(id=2, area="ห้องน้ำ", qr_token="inactive", is_active=False),
                ]
            )
            await session.commit()
            locations = await list_guest_repair_locations(session)
            assert [location.id for location in locations] == [1]
            resolved = await resolve_guest_repair_location_by_qr(session, qr_token=" active ")
            assert resolved.id == 1
            for token in ("inactive", "missing"):
                with pytest.raises(RepairLocationNotFoundError):
                    await resolve_guest_repair_location_by_qr(session, qr_token=token)
            response = await create_guest_repair_request(
                session,
                payload=payload(),
                image_uploads=[],
                storage=None,
            )
            assert response.request_type == RequestType.REPAIR
            assert response.request_code.startswith("RPR-")
            assert response.location == "ชั้น 2 ห้อง 201"
            assert response.image_count == 0
            request = await session.scalar(select(ServiceRequest))
            assert request.location_id == 1
            assert request.description == "ข้างลิฟต์ตัวซ้าย"
            assert request.reporter_email == "guest@example.com"
            assert await session.scalar(select(func.count()).select_from(RequestHistory)) == 1
            history = await session.scalar(select(RequestHistory))
            assert history.note == "Guest submitted repair request"
            assert history.performed_by is None
            tracked = await get_guest_repair_status(
                session,
                request_code=response.request_code.lower(),
                reporter_email=" GUEST@EXAMPLE.COM ",
            )
            assert tracked.request_type == RequestType.REPAIR
            assert "request_code" not in tracked.model_dump()
            with pytest.raises(RepairRequestNotFoundError):
                await get_guest_repair_status(
                    session,
                    request_code=response.request_code,
                    reporter_email="other@example.com",
                )
            request.request_type = RequestType.CLEANING
            await session.commit()
            with pytest.raises(RepairRequestNotFoundError):
                await get_guest_repair_status(
                    session,
                    request_code=response.request_code,
                    reporter_email="guest@example.com",
                )
            for location_id in (2, 999):
                with pytest.raises(RepairLocationNotFoundError):
                    await create_guest_repair_request(
                        session,
                        payload=payload(location_id=location_id),
                        image_uploads=[],
                        storage=None,
                    )
            assert await session.scalar(select(func.count()).select_from(ServiceRequest)) == 1

    asyncio.run(run())


def test_schema_normalization_defaults_and_description_boundary():
    value = GuestRepairCreate(
        title="  แอร์ไม่เย็น  ", reporter_email="Guest@EXAMPLE.COM", location_id=1
    )
    assert value.title == "แอร์ไม่เย็น"
    assert value.reporter_email == "guest@example.com"
    assert value.description == ""
    assert value.priority.value == "normal"
    assert payload(description="x" * 1000).description == "x" * 1000


@pytest.mark.parametrize("outcome", ["saved", "not_saved", "unknown", "cancel", "verify_cancel"])
def test_uncertain_commit_preserves_or_removes_image(test_context, monkeypatch, caplog, outcome):
    _, factory = test_context
    storage = FakeStorage()

    async def run():
        await seed_location(factory)
        async with factory() as session:
            original_commit = session.commit

            async def failed_commit():
                if outcome == "saved":
                    await original_commit()
                if outcome == "cancel":
                    raise asyncio.CancelledError()
                raise SQLAlchemyError("Commit acknowledgement lost")

            monkeypatch.setattr(session, "commit", failed_commit)
            if outcome in ("unknown", "verify_cancel"):
                error = (
                    SQLAlchemyError("Verification unavailable")
                    if outcome == "unknown"
                    else asyncio.CancelledError()
                )
                monkeypatch.setattr(
                    repair_guest, "_request_was_committed", AsyncMock(side_effect=error)
                )

            if outcome == "saved":
                response = await create_guest_repair_request(
                    session, payload=payload(), image_uploads=[image_upload()], storage=storage
                )
                assert response.request_code.startswith("RPR-")
                assert response.image_count == 1
            else:
                expected = (
                    asyncio.CancelledError
                    if outcome in ("cancel", "verify_cancel")
                    else RepairRequestPersistenceError
                )
                with pytest.raises(expected):
                    await create_guest_repair_request(
                        session, payload=payload(), image_uploads=[image_upload()], storage=storage
                    )
            assert not session.in_transaction()

        if outcome == "saved":
            async with factory() as session:
                assert await session.scalar(select(func.count()).select_from(ServiceRequest)) == 1
                assert await session.scalar(select(func.count()).select_from(Image)) == 1
        else:
            await assert_no_requests(factory)
        assert len(storage.objects) == (0 if outcome == "not_saved" else 1)
        assert len(storage.deleted) == (1 if outcome == "not_saved" else 0)
        if outcome in ("unknown", "cancel", "verify_cancel"):
            object_key = next(iter(storage.objects))
            assert object_key in caplog.text
            assert object_key.split("/")[1] in caplog.text

    asyncio.run(run())


def test_empty_locations_and_ordered_public_location_fields(test_context):
    _, factory = test_context

    async def run():
        async with factory() as session:
            assert await list_guest_repair_locations(session) == []
            session.add_all(
                [
                    Location(id=4, floor="3", area="ห้อง 101", qr_token="b"),
                    Location(id=3, floor="2", area="ห้อง 201", qr_token="a3"),
                    Location(id=2, floor="1", area="ห้อง 102", qr_token="a2"),
                    Location(id=1, floor="1", area="ห้อง 101", qr_token="a1"),
                    Location(id=5, floor="1", area="ห้อง 101", qr_token="a5"),
                    Location(id=6, floor="1", area="ห้อง 101", qr_token="closed", is_active=False),
                ]
            )
            await session.commit()
            locations = await list_guest_repair_locations(session)
            assert [location.id for location in locations] == [1, 5, 2, 3, 4]
            assert all("qr_token" not in location.model_dump() for location in locations)

    asyncio.run(run())


@pytest.mark.parametrize("expire_on_commit", [False, True])
def test_one_image_commits_with_response_ready_before_commit(
    test_context, monkeypatch, expire_on_commit
):
    _, factory = test_context
    storage = FakeStorage()

    async def run():
        await seed_location(factory)
        async with factory(expire_on_commit=expire_on_commit) as session:
            committed = False
            original_commit = session.commit
            original_refresh = session.refresh

            async def commit():
                nonlocal committed
                await original_commit()
                committed = True

            async def refresh(*args, **kwargs):
                if committed:
                    raise SQLAlchemyError("Database read after successful commit")
                return await original_refresh(*args, **kwargs)

            monkeypatch.setattr(session, "commit", commit)
            monkeypatch.setattr(session, "refresh", refresh)
            response = await create_guest_repair_request(
                session, payload=payload(), image_uploads=[image_upload()], storage=storage
            )
            assert committed
            assert response.created_at is not None
            assert response.image_count == 1
            assert response.location == "ห้อง 101"
            assert not session.in_transaction()

        async with factory() as session:
            request = await session.scalar(select(ServiceRequest))
            history = await session.scalar(select(RequestHistory))
            images = (await session.scalars(select(Image))).all()
            assert len(images) == 1
            image = images[0]
            assert response.request_code == request.request_code
            assert response.created_at == request.created_at
            assert history.request_id == image.request_id == request.id
            assert history.action == RequestAction.CREATED
            assert history.new_status == request.status == RequestStatus.WAITING
            assert image.image_type == ImageType.BEFORE
            assert image.object_key.startswith("repair/")
            assert image.lost_item_id is None
            assert image.bucket_name == "test"
            assert (image.width, image.height) == (32, 24)
            data, content_type = storage.objects[image.object_key]
            assert image.size_bytes == len(data)
            assert image.content_type == content_type == "image/webp"
            with PillowImage.open(BytesIO(data)) as decoded:
                assert decoded.format == "WEBP"
        assert len(storage.objects) == 1
        assert storage.deleted == []

    asyncio.run(run())


@pytest.mark.parametrize("failure_point", ["flush", "refresh", "response", "cancel"])
def test_failure_before_commit_rolls_back_and_deletes_image(
    test_context, monkeypatch, failure_point
):
    _, factory = test_context
    storage = FakeStorage()

    async def run():
        await seed_location(factory)
        async with factory() as session:
            if failure_point == "response":
                original_response = repair_guest.GuestRepairCreateResponse

                def invalid_response(**kwargs):
                    kwargs["created_at"] = None
                    return original_response(**kwargs)

                monkeypatch.setattr(repair_guest, "GuestRepairCreateResponse", invalid_response)
                expected_error = ValidationError
            elif failure_point == "cancel":
                monkeypatch.setattr(
                    session, "refresh", AsyncMock(side_effect=asyncio.CancelledError())
                )
                expected_error = asyncio.CancelledError
            else:
                monkeypatch.setattr(
                    session, failure_point, AsyncMock(side_effect=SQLAlchemyError("DB failure"))
                )
                expected_error = RepairRequestPersistenceError

            with pytest.raises(expected_error):
                await create_guest_repair_request(
                    session, payload=payload(), image_uploads=[image_upload()], storage=storage
                )
            assert not session.in_transaction()
        await assert_no_requests(factory)
        assert storage.objects == {}
        assert len(storage.deleted) == 1

    asyncio.run(run())


@pytest.mark.parametrize("failure_point", ["invalid_image", "storage"])
def test_upload_failure_leaves_no_request(test_context, monkeypatch, failure_point):
    _, factory = test_context
    storage = FakeStorage()

    async def run():
        await seed_location(factory)
        upload = image_upload()
        if failure_point == "invalid_image":
            await upload.close()
            upload = UploadFile(
                file=BytesIO(b"not an image"),
                filename="fake.png",
                headers=Headers({"content-type": "image/png"}),
            )
            expected_error = InvalidImageError
        else:
            monkeypatch.setattr(storage, "put", AsyncMock(side_effect=StorageOperationError("R2")))
            expected_error = StorageOperationError
        async with factory() as session:
            with pytest.raises(expected_error):
                await create_guest_repair_request(
                    session, payload=payload(), image_uploads=[upload], storage=storage
                )
            assert not session.in_transaction()
        await assert_no_requests(factory)
        assert storage.objects == {}
        assert storage.deleted == []

    asyncio.run(run())


@pytest.mark.parametrize(
    "location_id,request_type",
    [
        (None, RequestType.REPAIR),
        (999, RequestType.REPAIR),
        (1, None),
    ],
)
def test_database_enforces_location_and_type(test_context, location_id, request_type):
    _, factory = test_context

    async def run():
        async with factory() as session:
            session.add(Location(id=1, area="ห้อง 101", qr_token="active"))
            await session.commit()
            session.add(
                ServiceRequest(
                    request_code="RPR-TEST",
                    request_type=request_type,
                    location_id=location_id,
                    title="พื้นเปียก",
                    description="ข้างลิฟต์",
                    reporter_email="guest@example.com",
                )
            )
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()

    asyncio.run(run())
