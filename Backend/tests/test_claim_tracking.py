import asyncio
import re
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

from conftest import seed_staff
from test_cleaning_staff import login_staff

from app.models.enums import LostStatus, LostType
from app.models.lost_found import LostItem


def seed_context(test_context):
    client, factory = test_context
    seed_staff(factory, email="clerk@example.com", password="password", role="clerk")
    headers = login_staff(client, "clerk@example.com", "password")

    async def seed():
        async with factory() as session:
            session.add(
                LostItem(
                    item_code="FOUND-20261008-12345678",
                    report_type=LostType.FOUND,
                    item_category="Keys",
                    item_name="Keys",
                    description="Red keychain",
                    event_datetime=datetime.now(UTC),
                    location_detail="Lobby",
                    custody_location="Office",
                    private_verification_detail="SECRET-123",
                    reporter_email="finder@example.com",
                    status=LostStatus.APPROVED,
                )
            )
            await session.commit()

    asyncio.run(seed())
    created = client.post(
        "/api/v1/guest/found-items/FOUND-20261008-12345678/claims",
        json={
            "claimant_name": "Owner",
            "claimant_email": "owner@example.com",
            "proof_detail": "Original proof",
        },
    )
    assert created.status_code == 201, created.text
    return client, headers, created.json()


def test_tracking_additional_information_and_privacy(test_context):
    client, headers, claim = seed_context(test_context)
    code = claim["claim_code"]
    assert re.fullmatch(r"CLM-\d{8}-[0-9A-F]{8}", code)
    url = f"/api/v1/guest/claims/{code}"
    params = {"claimant_email": "OWNER@example.com"}
    assert client.get(url, params={"claimant_email": "wrong@example.com"}).status_code == 404
    assert client.get(url).status_code == 422
    initial = client.get(url, params=params).json()
    assert initial["custody_location"] is None
    assert not {"private_verification_detail", "review_note", "reporter_email"} & initial.keys()
    assert (
        client.post(
            url + "/additional-info",
            json={"claimant_email": "owner@example.com", "proof_detail": "new"},
        ).status_code
        == 409
    )
    requested = client.post(
        f"/api/v1/lost-found/ownership-requests/{claim['id']}/request-additional-info",
        headers=headers,
        json={"message": "Describe the keychain"},
    )
    assert requested.status_code == 200, requested.text
    waiting = client.get(url, params=params).json()
    assert waiting["staff_message"] == "Describe the keychain"
    assert waiting["status"] == "additional_info_required"
    assert (
        client.post(
            url + "/additional-info",
            json={"claimant_email": "wrong@example.com", "proof_detail": "Red"},
        ).status_code
        == 404
    )
    reply = client.post(
        url + "/additional-info",
        json={"claimant_email": "owner@example.com", "proof_detail": "Red keychain"},
    )
    assert reply.status_code == 200, reply.text
    assert reply.json()["status"] == "pending" and reply.json()["staff_message"] is None
    detail = client.get(
        f"/api/v1/lost-found/ownership-requests/{claim['id']}", headers=headers
    ).json()
    assert "Original proof" in detail["proof_detail"] and "Red keychain" in detail["proof_detail"]
    assert detail["claim_code"] == code
    assert (
        client.post(
            url + "/additional-info",
            json={"claimant_email": "owner@example.com", "proof_detail": "duplicate"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/api/v1/lost-found/ownership-requests/{claim['id']}/reject",
            headers=headers,
            json={"reason": "Proof does not match"},
        ).status_code
        == 200
    )
    result = client.get(url, params=params).json()
    assert result["status"] == "rejected" and result["staff_message"] == "Proof does not match"
    assert result["custody_location"] is None
    legacy = client.get(
        f"/api/v1/guest/found-items/{claim['found_item_code']}/claims/{claim['id']}", params=params
    )
    assert legacy.json()["claim_code"] == code


def test_scheduled_claim_and_email_privacy(test_context, monkeypatch):
    client, headers, claim = seed_context(test_context)
    from app.api.v1.endpoints import lost_found_clerk

    send = AsyncMock()
    monkeypatch.setattr(lost_found_clerk, "send_email", send)
    approved = client.post(
        f"/api/v1/lost-found/ownership-requests/{claim['id']}/approve", headers=headers
    )
    assert approved.status_code == 200, approved.text
    start = (datetime.now(ZoneInfo("Asia/Bangkok")) + timedelta(days=2)).replace(
        hour=9, minute=0, second=0, microsecond=0
    )
    while start.weekday() >= 5:
        start += timedelta(days=1)
    scheduled = client.post(
        f"/api/v1/lost-found/ownership-requests/{claim['id']}/schedule-pickup",
        headers=headers,
        json={
            "pickup_datetime": start.isoformat(),
            "pickup_end_datetime": (start + timedelta(hours=1)).isoformat(),
            "pickup_location": "Office",
            "note": "Bring confirmation",
        },
    )
    assert scheduled.status_code == 200, scheduled.text
    assert scheduled.json()["email_sent"] is True
    body = send.call_args.kwargs["body"]
    assert claim["claim_code"] in body
    assert (
        claim["id"] not in body
        and "SECRET-123" not in body
        and claim["found_item_code"] not in body
    )
    tracked = client.get(
        f"/api/v1/guest/claims/{claim['claim_code']}",
        params={"claimant_email": "owner@example.com"},
    ).json()
    assert tracked["status"] == "scheduled"
    assert tracked["custody_location"] == tracked["pickup_location"] == "Office"
    assert tracked["pickup_datetime"] and tracked["pickup_end_datetime"]
    assert tracked["pickup_note"] == "Bring confirmation"


def test_short_code_collision_retries_and_pending_info_blocks_duplicate(test_context, monkeypatch):
    from uuid import UUID, uuid4

    from app.services import lost_found_claim

    client, headers, first = seed_context(test_context)
    # Different UUID, identical short prefix to an existing claim.
    original = UUID(first["id"])
    collision = UUID(int=original.int ^ 1)
    candidates = iter([collision, uuid4()])
    monkeypatch.setattr(lost_found_claim, "uuid4", lambda: next(candidates))
    response = client.post(
        f"/api/v1/guest/found-items/{first['found_item_code']}/claims",
        json={
            "claimant_name": "Second owner",
            "claimant_email": "second@example.com",
            "proof_detail": "proof",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["claim_code"] != first["claim_code"]
    assert (
        client.post(
            f"/api/v1/lost-found/ownership-requests/{first['id']}/request-additional-info",
            headers=headers,
            json={"message": "More proof"},
        ).status_code
        == 200
    )
    duplicate = client.post(
        f"/api/v1/guest/found-items/{first['found_item_code']}/claims",
        json={
            "claimant_name": "Owner",
            "claimant_email": "owner@example.com",
            "proof_detail": "New claim",
        },
    )
    assert duplicate.status_code == 409
