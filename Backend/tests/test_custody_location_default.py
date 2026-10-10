"""Verification: the building has one custody point, so every fallback uses one default."""

import asyncio
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.core.config import Settings, settings
from app.models.enums import ClaimStatus, LostStatus, LostType, ReturnStatus
from app.models.lost_found import LostClaim, LostItem
from conftest import seed_staff
from test_guest_lost_found import (  # noqa: F401  (fake_storage is a pytest fixture)
    claim_form,
    fake_storage,
    found_form,
    lost_form,
)

SCHEDULE_PICKUP_URL = "/api/v1/lost-found/ownership-requests/{claim_id}/schedule-pickup"
PICKUP_TIME = "2030-09-20T13:30:00"


def _custody_of(session_factory, item_code):
    async def read():
        async with session_factory() as session:
            return await session.scalar(
                select(LostItem.custody_location).where(LostItem.item_code == item_code)
            )

    return asyncio.run(read())


def _clerk_headers(client, session_factory):
    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "clerk@example.com", "password": "admin-password"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _seed_verified_claim(session_factory, *, custody_location):
    async def seed():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND-CUSTODY",
                report_type=LostType.FOUND,
                item_category="Accessories",
                item_name="Bag",
                description="Black bag",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building A",
                custody_location=custody_location,
                reporter_email="finder@example.com",
                status=LostStatus.APPROVED,
            )
            session.add(item)
            await session.flush()
            claim = LostClaim(
                found_item_id=item.id,
                claimant_name="Owner User",
                claimant_email="owner@example.com",
                proof_detail="มีพวงกุญแจสีแดง",
                status=ClaimStatus.APPROVED,
                return_status=ReturnStatus.PENDING,
            )
            session.add(claim)
            await session.commit()
            return claim.id

    return asyncio.run(seed())


@pytest.fixture
def sent_emails(monkeypatch):
    emails = []

    async def fake_email(**kwargs):
        emails.append(kwargs)

    monkeypatch.setattr("app.api.v1.endpoints.lost_found_clerk.send_email", fake_email)
    return emails


def _pickup_location_line(body):
    return next(line for line in body.splitlines() if line.startswith("สถานที่รับคืน:"))


# V1
def test_default_custody_location_is_clerk_office_first_floor():
    assert Settings.model_fields["default_custody_location"].default == "ห้องธุรการ ชั้น 1"


# V2
def test_config_endpoint_returns_default_custody_location(test_context):
    client, _ = test_context

    response = client.get("/api/v1/guest/found-items/config")

    assert response.status_code == 200
    assert response.json() == {"custody_location": settings.default_custody_location}


# V3
def test_found_item_is_stored_at_default_custody_location(test_context, fake_storage):
    client, session_factory = test_context

    response = client.post("/api/v1/guest/found-items", data=found_form())

    assert response.status_code == 201
    assert _custody_of(session_factory, response.json()["item_code"]) == "ห้องธุรการ ชั้น 1"


# V4
def test_found_item_ignores_custody_location_sent_by_guest(test_context, fake_storage):
    client, session_factory = test_context

    response = client.post(
        "/api/v1/guest/found-items",
        data={**found_form(), "custody_location": "บ้านผู้แจ้ง"},
    )

    assert response.status_code == 201
    assert _custody_of(session_factory, response.json()["item_code"]) == "ห้องธุรการ ชั้น 1"


# V5
def test_lost_report_has_no_custody_location(test_context, fake_storage):
    client, session_factory = test_context

    response = client.post("/api/v1/guest/lost-items", data=lost_form())

    assert response.status_code == 201
    assert _custody_of(session_factory, response.json()["item_code"]) is None


# V6
def test_changing_setting_changes_config_and_new_items(test_context, fake_storage, monkeypatch):
    client, session_factory = test_context
    monkeypatch.setattr(settings, "default_custody_location", "ห้องทดสอบ ชั้น 2")

    config = client.get("/api/v1/guest/found-items/config")
    created = client.post("/api/v1/guest/found-items", data=found_form())

    assert config.json() == {"custody_location": "ห้องทดสอบ ชั้น 2"}
    assert _custody_of(session_factory, created.json()["item_code"]) == "ห้องทดสอบ ชั้น 2"


# V7
def test_claim_status_reveals_custody_location_only_after_approval(test_context, fake_storage):
    client, session_factory = test_context
    created = client.post("/api/v1/guest/found-items", data=found_form())
    item_code = created.json()["item_code"]

    async def approve_item():
        async with session_factory() as session:
            item = await session.scalar(select(LostItem).where(LostItem.item_code == item_code))
            item.status = LostStatus.APPROVED
            await session.commit()

    asyncio.run(approve_item())
    claim = client.post(f"/api/v1/guest/found-items/{item_code}/claims", json=claim_form())
    status_url = f"/api/v1/guest/found-items/{item_code}/claims/{claim.json()['id']}"
    params = {"claimant_email": "claimant@example.com"}

    pending = client.get(status_url, params=params)

    async def approve_claim():
        async with session_factory() as session:
            stored_claim = await session.scalar(select(LostClaim))
            stored_claim.status = ClaimStatus.APPROVED
            await session.commit()

    asyncio.run(approve_claim())
    approved = client.get(status_url, params=params)

    assert pending.json()["custody_location"] is None
    assert approved.json()["custody_location"] == "ห้องธุรการ ชั้น 1"


# V8
def test_pickup_email_uses_location_chosen_by_clerk(test_context, sent_emails):
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    claim_id = _seed_verified_claim(session_factory, custody_location="ห้องธุรการ ชั้น 1")

    response = client.post(
        SCHEDULE_PICKUP_URL.format(claim_id=claim_id),
        headers=headers,
        json={"pickup_datetime": PICKUP_TIME, "pickup_location": "ห้องประชุม 2"},
    )

    assert response.status_code == 200
    assert _pickup_location_line(sent_emails[0]["body"]) == "สถานที่รับคืน: ห้องประชุม 2"


# V9
def test_pickup_email_falls_back_to_item_custody_location(test_context, sent_emails):
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    claim_id = _seed_verified_claim(session_factory, custody_location="Clerk Office")

    response = client.post(
        SCHEDULE_PICKUP_URL.format(claim_id=claim_id),
        headers=headers,
        json={"pickup_datetime": PICKUP_TIME},
    )

    assert response.status_code == 200
    assert _pickup_location_line(sent_emails[0]["body"]) == "สถานที่รับคืน: Clerk Office"


# V10
@pytest.mark.parametrize("blank_location", [None, "   "])
def test_pickup_email_falls_back_to_default_for_old_item_without_custody(
    test_context, sent_emails, blank_location
):
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    claim_id = _seed_verified_claim(session_factory, custody_location=None)

    response = client.post(
        SCHEDULE_PICKUP_URL.format(claim_id=claim_id),
        headers=headers,
        json={"pickup_datetime": PICKUP_TIME, "pickup_location": blank_location},
    )

    body = sent_emails[0]["body"]
    assert response.status_code == 200
    assert _pickup_location_line(body) == "สถานที่รับคืน: ห้องธุรการ ชั้น 1"
    assert "ติดต่อห้องธุรการ CSB" not in body
