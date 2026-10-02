"""Acceptance tests for the admin clerk approval overview."""

import asyncio
from datetime import UTC, date, datetime, timedelta

from conftest import seed_staff
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.enums import LostStatus, LostType
from app.models.lost_found import LostItem


def _login_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login", json={"identifier": email, "password": password}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _item(
    code: str,
    report_type: LostType,
    status: LostStatus,
    created_at: datetime,
) -> LostItem:
    return LostItem(
        item_code=code,
        report_type=report_type,
        item_category="Test category",
        item_name=code,
        event_datetime=created_at,
        reporter_email="guest@example.com",
        status=status,
        created_at=created_at,
    )


def test_admin_can_view_aggregate_statistics_and_drill_into_metric(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, factory = test_context
    seed_staff(factory, email="admin@example.com", password="admin-password", role="admin")

    now = datetime.now(UTC)

    async def seed_announcements() -> None:
        async with factory() as session:
            session.add_all(
                (
                    _item("LOST-APPROVED", LostType.LOST, LostStatus.APPROVED, now),
                    _item(
                        "LOST-REJECTED", LostType.LOST, LostStatus.REJECTED, now + timedelta(minutes=1)
                    ),
                    _item(
                        "LOST-PENDING", LostType.LOST, LostStatus.PENDING, now - timedelta(hours=4)
                    ),
                    _item(
                        "FOUND-APPROVED", LostType.FOUND, LostStatus.APPROVED, now + timedelta(minutes=3)
                    ),
                    _item(
                        "FOUND-REJECTED", LostType.FOUND, LostStatus.REJECTED, now + timedelta(minutes=4)
                    ),
                )
            )
            await session.commit()

    asyncio.run(seed_announcements())
    headers = _login_headers(client, "admin@example.com", "admin-password")

    response = client.get("/api/v1/clerk-work-overview", headers=headers)
    assert response.status_code == 200
    overview = response.json()
    assert overview["summary"]["total"] == 5
    assert overview["summary"]["approved"] == 2
    assert overview["summary"]["rejected"] == 2
    assert overview["summary"]["pending_review"] == 1
    assert overview["summary"]["oldest_pending_review_age_hours"] >= 4
    assert overview["by_announcement_type"]["lost"]["pending_review"] == 1
    assert overview["by_announcement_type"]["found"]["pending_review"] == 0

    drill_down = client.get(
        "/api/v1/clerk-work-overview/announcements",
        headers=headers,
        params={"metric": "approved", "announcement_type": "lost"},
    )
    assert drill_down.status_code == 200
    body = drill_down.json()
    assert body["metric"] == "approved"
    assert body["announcement_type"] == "lost"
    assert body["total"] == 1
    assert body["announcements"][0]["item_code"] == "LOST-APPROVED"
    assert body["announcements"][0]["announcement_type"] == "lost"
    assert body["announcements"][0]["status"] == "approved"
    assert body["announcements"][0]["id"]
    assert body["announcements"][0]["submission_date"]

    pending = client.get(
        "/api/v1/clerk-work-overview/announcements",
        headers=headers,
        params={"metric": "pending_review", "announcement_type": "lost"},
    )
    assert pending.status_code == 200
    assert pending.json()["announcements"][0]["pending_review_age_hours"] >= 4


def test_admin_can_filter_clerk_metrics_by_submission_date_and_type(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, factory = test_context
    seed_staff(factory, email="admin@example.com", password="admin-password", role="admin")
    first_day = datetime(2026, 1, 10, 12, tzinfo=UTC)

    async def seed_announcements() -> None:
        async with factory() as session:
            session.add_all(
                (
                    _item("IN-RANGE", LostType.FOUND, LostStatus.APPROVED, first_day),
                    _item(
                        "OUT-OF-RANGE",
                        LostType.LOST,
                        LostStatus.REJECTED,
                        first_day + timedelta(days=1),
                    ),
                )
            )
            await session.commit()

    asyncio.run(seed_announcements())
    headers = _login_headers(client, "admin@example.com", "admin-password")
    params = {"date_from": "2026-01-10", "date_to": "2026-01-10", "announcement_type": "found"}
    overview = client.get("/api/v1/clerk-work-overview", headers=headers, params=params)
    assert overview.status_code == 200
    assert overview.json()["summary"]["total"] == 1
    assert overview.json()["summary"]["approved"] == 1
    assert overview.json()["date_from"] == "2026-01-10"

    list_response = client.get(
        "/api/v1/clerk-work-overview/announcements",
        headers=headers,
        params={**params, "metric": "total"},
    )
    assert [item["item_code"] for item in list_response.json()["announcements"]] == ["IN-RANGE"]

    invalid = client.get(
        "/api/v1/clerk-work-overview",
        headers=headers,
        params={"date_from": date(2026, 1, 11), "date_to": date(2026, 1, 10)},
    )
    assert invalid.status_code == 422
    assert invalid.json()["detail"] == "date_from must be on or before date_to"


def test_empty_clerk_work_overview_and_non_admin_access(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, factory = test_context
    seed_staff(factory, email="admin@example.com", password="admin-password", role="admin")
    seed_staff(factory, email="clerk@example.com", password="clerk-password", role="clerk")

    headers = _login_headers(client, "admin@example.com", "admin-password")
    overview = client.get("/api/v1/clerk-work-overview", headers=headers)
    assert overview.status_code == 200
    assert overview.json()["summary"] == {
        "total": 0,
        "approved": 0,
        "rejected": 0,
        "pending_review": 0,
        "oldest_pending_review_age_hours": None,
        "average_pending_review_age_hours": None,
    }

    announcements = client.get(
        "/api/v1/clerk-work-overview/announcements",
        headers=headers,
        params={"metric": "rejected"},
    )
    assert announcements.status_code == 200
    assert announcements.json() == {
        "metric": "rejected",
        "announcement_type": None,
        "date_from": None,
        "date_to": None,
        "total": 0,
        "announcements": [],
    }

    clerk_headers = _login_headers(client, "clerk@example.com", "clerk-password")
    assert client.get("/api/v1/clerk-work-overview", headers=clerk_headers).status_code == 403
