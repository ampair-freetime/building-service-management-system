"""Acceptance tests for admin cleaning/repair workload statistics."""

import asyncio

from conftest import seed_staff
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.enums import PriorityLevel, RequestAction, RequestStatus, RequestType
from app.models.location import Location
from app.models.service_request import RequestHistory, ServiceRequest


def _login_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    login = client.post(
        "/api/v1/auth/login", json={"identifier": email, "password": password}
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_admin_can_view_filtered_statistics_and_current_work(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, factory = test_context
    seed_staff(factory, email="admin@example.com", password="admin-password", role="admin")
    technician = seed_staff(
        factory, email="tech@example.com", password="tech-password", role="technician", full_name="Tech One"
    )
    cleaner = seed_staff(
        factory, email="cleaner@example.com", password="cleaner-password", role="housekeeper", full_name="Cleaner Zero"
    )

    async def create_work() -> None:
        async with factory() as session:
            location = Location(floor="1", area="Overview test area")
            session.add(location)
            await session.flush()

            current = ServiceRequest(
                request_code="OVERVIEW-OPEN",
                request_type=RequestType.REPAIR,
                location_id=location.id,
                title="Open repair",
                description="Still assigned",
                priority=PriorityLevel.NORMAL,
                status=RequestStatus.ASSIGNED,
                reporter_email="guest@example.com",
                assigned_staff_id=technician.id,
            )
            completed = ServiceRequest(
                request_code="OVERVIEW-CLOSED",
                request_type=RequestType.REPAIR,
                location_id=location.id,
                title="Closed repair",
                description="Completed by technician",
                priority=PriorityLevel.NORMAL,
                status=RequestStatus.COMPLETED,
                reporter_email="guest@example.com",
                assigned_staff_id=technician.id,
            )
            returned = ServiceRequest(
                request_code="OVERVIEW-RETURNED",
                request_type=RequestType.REPAIR,
                location_id=location.id,
                title="Returned repair",
                description="Returned to queue",
                priority=PriorityLevel.NORMAL,
                status=RequestStatus.WAITING,
                reporter_email="guest@example.com",
            )
            unassigned = ServiceRequest(
                request_code="OVERVIEW-UNASSIGNED",
                request_type=RequestType.CLEANING,
                location_id=location.id,
                title="Unassigned cleaning",
                description="Awaiting a cleaner",
                priority=PriorityLevel.NORMAL,
                status=RequestStatus.WAITING,
                reporter_email="guest@example.com",
            )
            session.add_all((current, completed, returned, unassigned))
            await session.flush()
            session.add_all(
                (
                    RequestHistory(
                        request_id=completed.id,
                        action=RequestAction.COMPLETED,
                        performed_by=technician.id,
                        target_staff_id=technician.id,
                        old_status=RequestStatus.IN_PROGRESS,
                        new_status=RequestStatus.COMPLETED,
                    ),
                    RequestHistory(
                        request_id=returned.id,
                        action=RequestAction.RETURNED,
                        performed_by=technician.id,
                        target_staff_id=technician.id,
                        old_status=RequestStatus.ASSIGNED,
                        new_status=RequestStatus.WAITING,
                    ),
                )
            )
            await session.commit()

    asyncio.run(create_work())
    headers = _login_headers(client, "admin@example.com", "admin-password")

    overview = client.get("/api/v1/staff-work-overview", headers=headers)
    assert overview.status_code == 200
    body = overview.json()
    assert body["summary"] == {
        "current_assigned": 1,
        "closed": 1,
        "returned": 1,
        "unassigned": 2,
    }

    repair = client.get(
        "/api/v1/staff-work-overview", headers=headers, params={"role": "repair", "search": "tech"}
    )
    assert repair.status_code == 200
    assert [item["id"] for item in repair.json()["staff"]] == [str(technician.id)]
    assert repair.json()["summary"] == {
        "current_assigned": 1,
        "closed": 1,
        "returned": 1,
        "unassigned": 1,
    }

    current_work = client.get(
        f"/api/v1/staff-work-overview/{technician.id}/current-work", headers=headers
    )
    assert current_work.status_code == 200
    assert current_work.json()["current_work_count"] == 1
    assert current_work.json()["current_work"][0]["request_code"] == "OVERVIEW-OPEN"

    empty = client.get(
        f"/api/v1/staff-work-overview/{cleaner.id}/current-work", headers=headers
    )
    assert empty.status_code == 200
    assert empty.json()["current_work_count"] == 0
    assert empty.json()["current_work"] == []


def test_only_admin_can_view_staff_work_overview(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, factory = test_context
    seed_staff(factory, email="tech@example.com", password="tech-password", role="technician")
    headers = _login_headers(client, "tech@example.com", "tech-password")

    assert client.get("/api/v1/staff-work-overview", headers=headers).status_code == 403
