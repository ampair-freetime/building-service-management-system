import asyncio

from conftest import seed_staff
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.location import Location


def seed_location(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def seed() -> None:
        async with session_factory() as session:
            session.add(
                Location(
                    id=1,
                    floor="2",
                    area="ห้อง 201",
                    qr_token="notification-test",
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


def test_housekeeper_receives_notification_when_cleaning_request_created(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="housekeeper@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "housekeeper@example.com",
        "correct-password",
    )

    # ก่อนมีคำร้อง ต้องยังไม่มี notification
    before = client.get(
        "/api/v1/notifications",
        headers=headers,
    )

    assert before.status_code == 200
    assert before.json() == []

    # Guest สร้าง cleaning request
    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "พื้นเปียก",
            "description": "ข้างลิฟต์ตัวซ้าย",
            "priority": "urgent",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    # Housekeeper ต้องได้รับ notification
    response = client.get(
        "/api/v1/notifications",
        headers=headers,
    )

    assert response.status_code == 200

    notifications = response.json()
    assert len(notifications) == 1

    notification = notifications[0]

    assert notification["title"] == "New cleaning request"
    assert created.json()["request_code"] in notification["message"]
    assert notification["request_id"] is not None
    assert notification["is_read"] is False

    # Mark notification as read
    marked = client.patch(
        f"/api/v1/notifications/{notification['id']}/read",
        headers=headers,
    )

    assert marked.status_code == 200
    assert marked.json()["id"] == notification["id"]
    assert marked.json()["is_read"] is True

    # GET อีกครั้งต้องเห็นว่าอ่านแล้ว
    after = client.get(
        "/api/v1/notifications",
        headers=headers,
    )

    assert after.status_code == 200
    assert after.json()[0]["is_read"] is True


def test_housekeeper_cannot_mark_another_housekeepers_notification_as_read(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        email="housekeeper1@example.com",
        password="password-one",
        role="housekeeper",
        full_name="House Keeper One",
    )

    seed_staff(
        session_factory,
        email="housekeeper2@example.com",
        password="password-two",
        role="housekeeper",
        full_name="House Keeper Two",
    )

    hk1_headers = login_staff(
        client,
        "housekeeper1@example.com",
        "password-one",
    )

    hk2_headers = login_staff(
        client,
        "housekeeper2@example.com",
        "password-two",
    )

    # Guest สร้าง request -> housekeeper ทั้งสองคนจะได้ notification
    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ถังขยะเต็ม",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    hk1_notifications = client.get(
        "/api/v1/notifications",
        headers=hk1_headers,
    )

    assert hk1_notifications.status_code == 200
    assert len(hk1_notifications.json()) == 1

    hk1_notification_id = hk1_notifications.json()[0]["id"]

    # HK002 พยายาม mark notification ของ HK001
    response = client.patch(
        f"/api/v1/notifications/{hk1_notification_id}/read",
        headers=hk2_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"

    # ของ HK001 ต้องยัง unread
    hk1_after = client.get(
        "/api/v1/notifications",
        headers=hk1_headers,
    )

    assert hk1_after.json()[0]["is_read"] is False