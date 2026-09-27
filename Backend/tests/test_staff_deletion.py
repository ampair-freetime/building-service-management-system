"""Acceptance tests for secure, history-preserving staff deletion."""

import asyncio

from conftest import seed_staff
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.enums import PriorityLevel, RequestStatus, RequestType
from app.models.location import Location
from app.models.service_request import ServiceRequest
from app.models.staff_deletion_audit import StaffDeletionAudit


def _login_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    login = client.post(
        "/api/v1/auth/login", json={"identifier": email, "password": password}
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _admin_headers(
    client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> dict[str, str]:
    seed_staff(factory, email="admin@example.com", password="admin-password", role="admin")
    return _login_headers(client, "admin@example.com", "admin-password")


def test_delete_hides_account_revokes_existing_session_and_writes_audit(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, factory = test_context
    admin_headers = _admin_headers(client, factory)
    target = seed_staff(
        factory, email="former@example.com", password="former-password", role="technician"
    )
    former_headers = _login_headers(client, "former@example.com", "former-password")

    deleted = client.delete(f"/api/v1/staff/{target.id}", headers=admin_headers)

    assert deleted.status_code == 204
    assert "former@example.com" not in {
        account["email"] for account in client.get("/api/v1/staff", headers=admin_headers).json()
    }
    assert client.post(
        "/api/v1/auth/login",
        json={"identifier": "former@example.com", "password": "former-password"},
    ).status_code == 401
    assert client.get("/api/v1/auth/me", headers=former_headers).status_code == 401

    async def assert_audit() -> None:
        async with factory() as session:
            audit = await session.scalar(
                select(StaffDeletionAudit).where(StaffDeletionAudit.deleted_staff_id == target.id)
            )
            assert audit is not None
            assert audit.deleted_email == "former@example.com"

    asyncio.run(assert_audit())


def test_delete_requires_unfinished_work_to_be_reassigned(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, factory = test_context
    admin_headers = _admin_headers(client, factory)
    target = seed_staff(factory, email="worker@example.com", password="worker-password", role="technician")

    async def assign_work() -> None:
        async with factory() as session:
            location = Location(floor="1", area="Deletion test area")
            session.add(location)
            await session.flush()
            session.add(
                ServiceRequest(
                    request_code="DELETE-001",
                    request_type=RequestType.REPAIR,
                    location_id=location.id,
                    title="Unfinished assignment",
                    description="Must be reassigned first",
                    priority=PriorityLevel.NORMAL,
                    status=RequestStatus.ASSIGNED,
                    reporter_email="guest@example.com",
                    assigned_staff_id=target.id,
                )
            )
            await session.commit()

    asyncio.run(assign_work())
    blocked = client.delete(f"/api/v1/staff/{target.id}", headers=admin_headers)

    assert blocked.status_code == 409
    assert blocked.json()["detail"]["unfinished_assignments"][0]["request_code"] == "DELETE-001"


def test_admin_cannot_delete_self_or_last_active_admin(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, factory = test_context
    headers = _admin_headers(client, factory)
    admin = next(item for item in client.get("/api/v1/staff", headers=headers).json() if item["role"] == "admin")

    self_delete = client.delete(f"/api/v1/staff/{admin['id']}", headers=headers)
    assert self_delete.status_code == 409
    assert self_delete.json()["detail"] == "You cannot delete your own account"

    second_admin = seed_staff(
        factory, email="admin2@example.com", password="admin2-password", role="admin"
    )
    deleted_second = client.delete(f"/api/v1/staff/{second_admin.id}", headers=headers)
    assert deleted_second.status_code == 204


def test_non_admin_cannot_delete_staff(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, factory = test_context
    target = seed_staff(factory, email="target@example.com", password="target-password", role="clerk")
    seed_staff(factory, email="worker@example.com", password="worker-password", role="technician")
    worker_headers = _login_headers(client, "worker@example.com", "worker-password")

    assert client.delete(f"/api/v1/staff/{target.id}", headers=worker_headers).status_code == 403
    assert client.post(
        "/api/v1/auth/login",
        json={"identifier": "target@example.com", "password": "target-password"},
    ).status_code == 200
