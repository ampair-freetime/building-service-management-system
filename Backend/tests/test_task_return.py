"""Staff return an accepted cleaning/repair task to the shared queue."""

import asyncio
from uuid import UUID

import pytest
from conftest import seed_staff
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.enums import RequestAction, RequestStatus, RequestType
from app.models.location import Location
from app.models.service_request import RequestHistory, ServiceRequest

PASSWORD = "Staff-Pass1!"
Context = tuple[TestClient, async_sessionmaker[AsyncSession]]

# (request type, API prefix, staff role)
KINDS = [
    (RequestType.CLEANING, "/api/v1/cleaning-tasks", "housekeeper"),
    (RequestType.REPAIR, "/api/v1/repair-requests", "technician"),
]


def _headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"identifier": email, "password": PASSWORD})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _seed_task(factory, request_type: RequestType) -> UUID:
    async def seed() -> UUID:
        async with factory() as session:
            session.add(Location(id=1, floor="2", area="ห้อง 201"))
            task = ServiceRequest(
                request_code="TASK-0001",
                request_type=request_type,
                location_id=1,
                title="Task to return",
                description="Description",
                reporter_email="guest@example.com",
            )
            session.add(task)
            await session.commit()
            return task.id

    return asyncio.run(seed())


def _load(factory, task_id: UUID) -> tuple[ServiceRequest, list[RequestHistory]]:
    async def load():
        async with factory() as session:
            task = await session.get(ServiceRequest, task_id)
            history = list(
                await session.scalars(
                    select(RequestHistory)
                    .where(RequestHistory.request_id == task_id)
                    .order_by(RequestHistory.created_at, RequestHistory.id)
                )
            )
            return task, history

    return asyncio.run(load())


def _set_status(factory, task_id: UUID, new_status: RequestStatus) -> None:
    async def change():
        async with factory() as session:
            await session.execute(
                update(ServiceRequest)
                .where(ServiceRequest.id == task_id)
                .values(status=new_status)
            )
            await session.commit()

    asyncio.run(change())


@pytest.fixture(params=KINDS, ids=["cleaning", "repair"])
def setup(request, test_context: Context):
    request_type, prefix, role = request.param
    client, factory = test_context
    first = seed_staff(factory, email="first@example.com", password=PASSWORD, role=role)
    second = seed_staff(factory, email="second@example.com", password=PASSWORD, role=role)
    task_id = _seed_task(factory, request_type)
    return {
        "client": client,
        "factory": factory,
        "prefix": prefix,
        "task_id": task_id,
        "first": first,
        "second": second,
        "first_headers": _headers(client, "first@example.com"),
        "second_headers": _headers(client, "second@example.com"),
    }


def _accept(s, headers):
    return s["client"].patch(f"{s['prefix']}/{s['task_id']}/accept", headers=headers)


def _return(s, headers, **body):
    payload = {"reason": "ติดภารกิจด่วน", "note": "ต้องออกไปอีกอาคาร", **body}
    return s["client"].post(f"{s['prefix']}/{s['task_id']}/return", headers=headers, json=payload)


@pytest.mark.parametrize(
    "status_before", [RequestStatus.ASSIGNED, RequestStatus.RECEIVED, RequestStatus.IN_PROGRESS]
)
def test_return_releases_task_and_records_history(setup, status_before) -> None:
    s = setup
    assert _accept(s, s["first_headers"]).status_code == 200
    _set_status(s["factory"], s["task_id"], status_before)

    response = _return(s, s["first_headers"])
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "waiting"
    assert body["assigned_staff"] is None

    task, history = _load(s["factory"], s["task_id"])
    assert task.status == RequestStatus.WAITING
    assert task.assigned_staff_id is None
    [returned] = [entry for entry in history if entry.action == RequestAction.RETURNED]
    assert returned.performed_by == s["first"].id
    assert returned.target_staff_id == s["first"].id
    assert returned.old_status == status_before
    assert returned.new_status == RequestStatus.WAITING
    assert returned.note == "ติดภารกิจด่วน — ต้องออกไปอีกอาคาร"


def test_another_staff_can_accept_after_return(setup) -> None:
    s = setup
    assert _accept(s, s["first_headers"]).status_code == 200
    # Before the fix this was the bug: the second staff got 409 forever.
    assert _accept(s, s["second_headers"]).status_code == 409
    assert _return(s, s["first_headers"]).status_code == 200

    accepted = _accept(s, s["second_headers"])
    assert accepted.status_code == 200
    assert accepted.json()["assigned_staff"]["id"] == str(s["second"].id)
    task, _ = _load(s["factory"], s["task_id"])
    assert task.assigned_staff_id == s["second"].id


def test_same_staff_can_accept_again_after_return(setup) -> None:
    s = setup
    assert _accept(s, s["first_headers"]).status_code == 200
    assert _return(s, s["first_headers"]).status_code == 200
    response = _accept(s, s["first_headers"])
    assert response.status_code == 200
    task, history = _load(s["factory"], s["task_id"])
    assert task.assigned_staff_id == s["first"].id
    assert task.status == RequestStatus.ASSIGNED
    assert sum(entry.action == RequestAction.RETURNED for entry in history) == 1
    assert sum(entry.action == RequestAction.ACCEPTED for entry in history) == 2


def test_only_the_assigned_staff_can_return(setup) -> None:
    s = setup
    assert _accept(s, s["first_headers"]).status_code == 200

    assert _return(s, s["second_headers"]).status_code == 403
    task, _ = _load(s["factory"], s["task_id"])
    assert task.assigned_staff_id == s["first"].id


@pytest.mark.parametrize(
    "status_after", [RequestStatus.COMPLETED, RequestStatus.CANCELLED]
)
def test_closed_task_cannot_be_returned(setup, status_after) -> None:
    s = setup
    assert _accept(s, s["first_headers"]).status_code == 200
    _set_status(s["factory"], s["task_id"], status_after)

    assert _return(s, s["first_headers"]).status_code == 409
    task, _ = _load(s["factory"], s["task_id"])
    assert task.status == status_after
    assert task.assigned_staff_id == s["first"].id


def test_unassigned_or_unknown_task_cannot_be_returned(setup) -> None:
    s = setup
    # Nobody accepted it yet: the caller does not own it.
    assert _return(s, s["first_headers"]).status_code == 403
    missing = s["client"].post(
        f"{s['prefix']}/00000000-0000-0000-0000-000000000000/return",
        headers=s["first_headers"],
        json={"reason": "x"},
    )
    assert missing.status_code == 404


def test_reason_is_required(setup) -> None:
    s = setup
    assert _accept(s, s["first_headers"]).status_code == 200
    assert _return(s, s["first_headers"], reason="   ").status_code == 422
    response = s["client"].post(
        f"{s['prefix']}/{s['task_id']}/return", headers=s["first_headers"], json={}
    )
    assert response.status_code == 422


def test_note_is_optional(setup) -> None:
    s = setup
    assert _accept(s, s["first_headers"]).status_code == 200
    assert _return(s, s["first_headers"], note="  ").status_code == 200
    _, history = _load(s["factory"], s["task_id"])
    [returned] = [entry for entry in history if entry.action == RequestAction.RETURNED]
    assert returned.note == "ติดภารกิจด่วน"


def test_wrong_role_cannot_use_the_other_queue(test_context: Context) -> None:
    client, factory = test_context
    seed_staff(factory, email="cleaner@example.com", password=PASSWORD, role="housekeeper")
    task_id = _seed_task(factory, RequestType.REPAIR)
    headers = _headers(client, "cleaner@example.com")
    response = client.post(
        f"/api/v1/repair-requests/{task_id}/return", headers=headers, json={"reason": "x"}
    )
    assert response.status_code == 403
    # A cleaning endpoint must not find a repair task either.
    response = client.post(
        f"/api/v1/cleaning-tasks/{task_id}/return", headers=headers, json={"reason": "x"}
    )
    assert response.status_code == 404


def test_work_overview_counts_returned_tasks(test_context: Context) -> None:
    client, factory = test_context
    seed_staff(factory, email="admin@example.com", password=PASSWORD, role="admin")
    cleaner = seed_staff(
        factory, email="cleaner@example.com", password=PASSWORD, role="housekeeper"
    )
    task_id = _seed_task(factory, RequestType.CLEANING)
    headers = _headers(client, "cleaner@example.com")
    assert client.patch(f"/api/v1/cleaning-tasks/{task_id}/accept", headers=headers).status_code == 200
    assert (
        client.post(
            f"/api/v1/cleaning-tasks/{task_id}/return", headers=headers, json={"reason": "x"}
        ).status_code
        == 200
    )

    overview = client.get(
        "/api/v1/staff-work-overview", headers=_headers(client, "admin@example.com")
    ).json()
    assert overview["summary"]["returned"] == 1
    assert overview["summary"]["current_assigned"] == 0
    assert overview["summary"]["unassigned"] == 1
    [row] = [item for item in overview["staff"] if item["id"] == str(cleaner.id)]
    assert row["counts"]["returned"] == 1
