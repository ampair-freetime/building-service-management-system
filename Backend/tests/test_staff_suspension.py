"""Acceptance tests for suspending and reactivating staff accounts."""

import asyncio

from conftest import seed_staff
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.enums import PriorityLevel, RequestStatus, RequestType
from app.models.location import Location
from app.models.service_request import ServiceRequest

Context = tuple[TestClient, async_sessionmaker[AsyncSession]]


def _login(client: TestClient, email: str, password: str):
    return client.post("/api/v1/auth/login", json={"identifier": email, "password": password})


def _headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    login = _login(client, email, password)
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _admin_headers(client: TestClient, factory: async_sessionmaker[AsyncSession]):
    seed_staff(factory, email="admin@example.com", password="admin-password", role="admin")
    return _headers(client, "admin@example.com", "admin-password")


def _set_status(client: TestClient, staff_id, status: str, headers):
    return client.patch(f"/api/v1/staff/{staff_id}/status", headers=headers, json={"status": status})


def test_suspend_blocks_login_and_existing_token_then_reactivate_restores_access(
    test_context: Context,
) -> None:
    client, factory = test_context
    admin = _admin_headers(client, factory)
    target = seed_staff(factory, email="clerk@example.com", password="clerk-password", role="clerk")
    clerk = _headers(client, "clerk@example.com", "clerk-password")

    suspended = _set_status(client, target.id, "suspended", admin)
    assert suspended.status_code == 200
    assert suspended.json()["status"] == "suspended"

    # token ที่ออกไปก่อนถูกระงับต้องใช้ไม่ได้ทันที ไม่ต้องรอหมดอายุ
    assert client.get("/api/v1/auth/me", headers=clerk).status_code == 401
    assert _login(client, "clerk@example.com", "clerk-password").status_code == 401
    listed = client.get("/api/v1/staff", headers=admin).json()
    assert next(item for item in listed if item["id"] == str(target.id))["status"] == "suspended"

    # กดซ้ำได้ผลเหมือนเดิม ไม่ error
    assert _set_status(client, target.id, "suspended", admin).status_code == 200

    reactivated = _set_status(client, target.id, "active", admin)
    assert reactivated.status_code == 200
    assert reactivated.json()["status"] == "active"
    assert _login(client, "clerk@example.com", "clerk-password").status_code == 200


def test_suspend_requires_unfinished_work_to_be_reassigned(test_context: Context) -> None:
    client, factory = test_context
    admin = _admin_headers(client, factory)
    target = seed_staff(
        factory, email="worker@example.com", password="worker-password", role="technician"
    )

    async def assign_work() -> None:
        async with factory() as session:
            location = Location(floor="1", area="Suspension test area")
            session.add(location)
            await session.flush()
            session.add(
                ServiceRequest(
                    request_code="SUSPEND-001",
                    request_type=RequestType.REPAIR,
                    location_id=location.id,
                    title="Unfinished assignment",
                    description="Must be reassigned first",
                    priority=PriorityLevel.NORMAL,
                    status=RequestStatus.IN_PROGRESS,
                    reporter_email="guest@example.com",
                    assigned_staff_id=target.id,
                )
            )
            await session.commit()

    asyncio.run(assign_work())
    blocked = _set_status(client, target.id, "suspended", admin)
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["unfinished_assignments"][0]["request_code"] == "SUSPEND-001"
    assert _login(client, "worker@example.com", "worker-password").status_code == 200


def test_admin_cannot_suspend_self_and_other_admin_can_be_suspended(test_context: Context) -> None:
    client, factory = test_context
    admin = _admin_headers(client, factory)
    me = client.get("/api/v1/auth/me", headers=admin).json()

    self_suspend = _set_status(client, me["id"], "suspended", admin)
    assert self_suspend.status_code == 409
    assert self_suspend.json()["detail"] == "You cannot change your own account status"

    other = seed_staff(factory, email="admin2@example.com", password="admin2-password", role="admin")
    assert _set_status(client, other.id, "suspended", admin).status_code == 200
    assert _login(client, "admin2@example.com", "admin2-password").status_code == 401


def test_status_endpoint_validation_and_authorization(test_context: Context) -> None:
    client, factory = test_context
    admin = _admin_headers(client, factory)
    target = seed_staff(factory, email="target@example.com", password="target-password", role="clerk")
    seed_staff(factory, email="tech@example.com", password="tech-password", role="technician")
    tech = _headers(client, "tech@example.com", "tech-password")

    assert _set_status(client, target.id, "suspended", tech).status_code == 403
    assert client.patch(
        f"/api/v1/staff/{target.id}/status", json={"status": "suspended"}
    ).status_code == 401
    assert _set_status(client, target.id, "deleted", admin).status_code == 422
    assert _set_status(client, target.id, "paused", admin).status_code == 422
    assert client.patch(
        f"/api/v1/staff/{target.id}/status",
        headers=admin,
        json={"status": "suspended", "role": "admin"},
    ).status_code == 422
    assert _login(client, "target@example.com", "target-password").status_code == 200

    assert client.delete(f"/api/v1/staff/{target.id}", headers=admin).status_code == 204
    assert _set_status(client, target.id, "active", admin).status_code == 404
