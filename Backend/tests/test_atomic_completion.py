"""Completion must persist the report, status and images together."""

import asyncio
from uuid import uuid4

import pytest
from conftest import seed_staff
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from test_cleaning_staff import FakeStorage, login_staff, make_png

from app.api.dependencies import provide_optional_object_storage
from app.models.enums import RequestAction, RequestStatus, RequestType
from app.models.image import Image
from app.models.location import Location
from app.models.service_request import RequestHistory, ServiceRequest
from app.services.object_storage import StorageOperationError


@pytest.fixture(
    params=[
        ("cleaning", "housekeeper", "cleaning-tasks"),
        ("repair", "technician", "repair-requests"),
    ]
)
def task_context(test_context, request):
    client, factory = test_context
    kind, role, route = request.param
    staff = seed_staff(factory, email="worker@example.com", password="password", role=role)
    headers = login_staff(client, "worker@example.com", "password")
    task_id = uuid4()

    async def seed():
        async with factory() as session:
            session.add(Location(id=1, floor="1", area="Lobby"))
            await session.flush()
            session.add(
                ServiceRequest(
                    id=task_id,
                    request_code=f"TEST-{kind}",
                    request_type=RequestType(kind),
                    location_id=1,
                    title="Test",
                    description="",
                    reporter_email="guest@example.com",
                    assigned_staff_id=staff.id,
                    status=RequestStatus.IN_PROGRESS,
                )
            )
            await session.commit()

    asyncio.run(seed())
    storage = FakeStorage()
    client.app.dependency_overrides[provide_optional_object_storage] = lambda: storage
    return client, factory, f"/api/v1/{route}/{task_id}", task_id, headers, storage


def rows(factory, task_id):
    async def read():
        async with factory() as session:
            task = await session.get(ServiceRequest, task_id)
            history = list(
                await session.scalars(
                    select(RequestHistory).where(RequestHistory.request_id == task_id)
                )
            )
            images = list(await session.scalars(select(Image).where(Image.request_id == task_id)))
            return task, history, images

    return asyncio.run(read())


def test_complete_commits_report_and_photo_and_rejects_repeat(task_context):
    client, factory, url, task_id, headers, storage = task_context
    response = client.post(
        url + "/complete",
        headers=headers,
        data={"note": " Fixed "},
        files=[("image", ("after.png", make_png(), "image/png"))],
    )
    assert response.status_code == 200, response.text
    task, history, images = rows(factory, task_id)
    assert task.status == RequestStatus.COMPLETED and task.completed_at
    assert {entry.action for entry in history} == {
        RequestAction.COMPLETED,
        RequestAction.COMPLETION_NOTE_ADDED,
    }
    assert (
        next(entry.note for entry in history if entry.action == RequestAction.COMPLETION_NOTE_ADDED)
        == "Fixed"
    )
    assert len(images) == len(storage.objects) == 1
    assert (
        client.post(url + "/complete", headers=headers, data={"note": "Duplicate"}).status_code
        == 409
    )
    assert len(rows(factory, task_id)[1]) == 2
    listing = client.get(url.rsplit("/", 1)[0], headers=headers).json()
    assert listing["requests"][0]["has_completion_report"] is True


@pytest.mark.parametrize("note", ["", "   ", "x" * 2001])
def test_invalid_report_cannot_complete(task_context, note):
    client, factory, url, task_id, headers, _ = task_context
    assert client.post(url + "/complete", headers=headers, data={"note": note}).status_code == 422
    task, history, images = rows(factory, task_id)
    assert task.status == RequestStatus.IN_PROGRESS
    assert not history and not images


def test_invalid_photo_leaves_no_report_or_objects(task_context):
    client, factory, url, task_id, headers, storage = task_context
    response = client.post(
        url + "/complete",
        headers=headers,
        data={"note": "Fixed"},
        files=[
            ("image", ("valid.png", make_png(), "image/png")),
            ("image", ("bad.png", b"not an image", "image/png")),
        ],
    )
    assert response.status_code == 422
    task, history, images = rows(factory, task_id)
    assert task.status == RequestStatus.IN_PROGRESS and task.completed_at is None
    assert not history and not images and not storage.objects


def test_storage_failure_rolls_back_and_removes_uploaded_objects(task_context, monkeypatch):
    client, factory, url, task_id, headers, storage = task_context
    original = storage.put
    count = 0

    async def fail_second(**kwargs):
        nonlocal count
        count += 1
        result = await original(**kwargs)
        if count == 2:
            raise StorageOperationError("failed after remote write")
        return result

    monkeypatch.setattr(storage, "put", fail_second)
    response = client.post(
        url + "/complete",
        headers=headers,
        data={"note": "Fixed"},
        files=[
            ("image", ("one.png", make_png(), "image/png")),
            ("image", ("two.png", make_png(), "image/png")),
        ],
    )
    assert response.status_code == 502
    task, history, images = rows(factory, task_id)
    assert task.status == RequestStatus.IN_PROGRESS and task.completed_at is None
    assert not history and not images and not storage.objects
    assert len(storage.deleted) == 2


def test_database_failure_cleans_storage_and_rolls_back(task_context, monkeypatch):
    client, factory, url, task_id, headers, storage = task_context

    async def fail_commit(self):
        raise SQLAlchemyError("commit failed")

    monkeypatch.setattr(AsyncSession, "commit", fail_commit)
    with pytest.raises(SQLAlchemyError):
        client.post(
            url + "/complete",
            headers=headers,
            data={"note": "Fixed"},
            files=[("image", ("after.png", make_png(), "image/png"))],
        )
    task, history, images = rows(factory, task_id)
    assert task.status == RequestStatus.IN_PROGRESS and task.completed_at is None
    assert not history and not images and not storage.objects


def test_old_status_route_cannot_bypass_report(task_context):
    client, factory, url, task_id, headers, _ = task_context
    assert (
        client.patch(url + "/status", headers=headers, json={"status": "completed"}).status_code
        == 409
    )
    assert rows(factory, task_id)[0].status == RequestStatus.IN_PROGRESS
    if "repair-requests" in url:
        assert client.patch(url + "/complete", headers=headers).status_code == 422


def test_too_many_images_and_wrong_owner_leave_task_untouched(task_context):
    client, factory, url, task_id, headers, storage = task_context
    from app.core.config import settings

    files = [
        ("image", (f"{i}.png", make_png(), "image/png"))
        for i in range(settings.max_guest_images + 1)
    ]
    assert (
        client.post(
            url + "/complete", headers=headers, data={"note": "Report"}, files=files
        ).status_code
        == 422
    )
    role = "technician" if "repair-requests" in url else "housekeeper"
    seed_staff(factory, email="other@example.com", password="password", role=role)
    other = login_staff(client, "other@example.com", "password")
    assert client.post(url + "/complete", headers=other, data={"note": "Report"}).status_code == 403
    task, history, images = rows(factory, task_id)
    assert task.status == RequestStatus.IN_PROGRESS
    assert not history and not images and not storage.objects
