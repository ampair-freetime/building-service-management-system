import asyncio
from datetime import datetime, timezone

from conftest import seed_staff
from app.models.enums import LostStatus, LostType
from app.models.lost_found import LostItem


def test_administrative_can_view_found_item_detail(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        staff_code="ADMINISTRATIVE001",
        email="administrative@example.com",
        password="admin-password",
        role="administrative",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "ADMINISTRATIVE001",
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