import asyncio
from datetime import datetime, timezone

from conftest import seed_staff
from app.models.enums import LostStatus, LostType
from app.models.lost_found import LostItem


def test_administrative_can_list_pending_found_items(test_context):
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
                item_code="FOUND001",
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

    asyncio.run(seed_item())

    response = client.get(
        "/api/v1/lost-found/pending-found-items",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["item_code"] == "FOUND001"
    assert data[0]["report_type"] == "found"
    assert data[0]["status"] == "pending"