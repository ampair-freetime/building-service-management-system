import asyncio
from datetime import datetime, timezone

from uuid import uuid4
from conftest import seed_staff
from app.models.enums import LostStatus, LostType
from app.models.lost_found import LostItem


def test_administrative_can_view_found_item_detail(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        staff_code="CLERK001",
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "CLERK001",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_item():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND002",
                report_type=LostType.FOUND,
                item_category="Electronics",
                item_name="Laptop",
                description="Silver laptop",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building B",
                custody_location="Administrative Office",
                reporter_email="user@example.com",
                status=LostStatus.PENDING,
            )
            session.add(item)
            await session.commit()
            await session.refresh(item)
            return item.id

    item_id = asyncio.run(seed_item())

    response = client.get(
        f"/api/v1/lost-found/found-items/{item_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["item_code"] == "FOUND002"
    assert data["report_type"] == "found"
    assert data["item_name"] == "Laptop"
    assert data["item_category"] == "Electronics"
    assert data["description"] == "Silver laptop"
    assert data["location_detail"] == "Building B"
    assert data["custody_location"] == "Administrative Office"
    assert data["status"] == "pending"


def test_administrative_can_approve_found_item(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        staff_code="CLERK001",
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "CLERK001",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_item():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND003",
                report_type=LostType.FOUND,
                item_category="Electronics",
                item_name="Phone",
                description="Black phone",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building A",
                custody_location="Administrative Office",
                reporter_email="user@example.com",
                status=LostStatus.PENDING,
            )

            session.add(item)
            await session.commit()
            await session.refresh(item)

            return item.id

    item_id = asyncio.run(seed_item())

    response = client.post(
        f"/api/v1/lost-found/found-items/{item_id}/approve",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(item_id)
    assert data["report_type"] == "found"
    assert data["status"] == "approved"


def test_cannot_approve_already_approved_found_item(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        staff_code="CLERK001",
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "CLERK001",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_item():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND004",
                report_type=LostType.FOUND,
                item_category="Accessories",
                item_name="Wallet",
                description="Brown wallet",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building C",
                custody_location="Administrative Office",
                reporter_email="user@example.com",
                status=LostStatus.APPROVED,
            )

            session.add(item)
            await session.commit()
            await session.refresh(item)

            return item.id

    item_id = asyncio.run(seed_item())

    response = client.post(
        f"/api/v1/lost-found/found-items/{item_id}/approve",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Pending found item not found"


def test_cannot_approve_lost_item(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        staff_code="CLERK001",
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "CLERK001",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_item():
        async with session_factory() as session:
            item = LostItem(
                item_code="LOST001",
                report_type=LostType.LOST,
                item_category="Accessories",
                item_name="Wallet",
                description="Black wallet",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building A",
                custody_location=None,
                reporter_email="user@example.com",
                status=LostStatus.PENDING,
            )

            session.add(item)
            await session.commit()
            await session.refresh(item)

            return item.id

    item_id = asyncio.run(seed_item())

    response = client.post(
        f"/api/v1/lost-found/found-items/{item_id}/approve",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Pending found item not found"


def test_cannot_approve_nonexistent_found_item(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        staff_code="CLERK001",
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "CLERK001",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    missing_item_id = uuid4()

    response = client.post(
        f"/api/v1/lost-found/found-items/{missing_item_id}/approve",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Pending found item not found"