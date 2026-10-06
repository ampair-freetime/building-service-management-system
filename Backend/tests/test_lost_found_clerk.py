import asyncio
from datetime import datetime, timezone

from uuid import uuid4
from unittest.mock import Mock

import pytest

from app.api.dependencies import provide_object_storage, provide_optional_object_storage
from conftest import seed_staff
from sqlalchemy import select
from app.models.enums import ClaimStatus, LostStatus, LostType, ReturnStatus
from app.models.image import Image
from app.models.lost_found import (
    LostClaim,
    LostClaimReturnStatusHistory,
    LostItem,
)


@pytest.fixture
def public_list_storage(test_context):
    """Public-list regression tests ต้องไม่ขึ้นกับการตั้งค่า R2 จริง."""
    client, _ = test_context
    client.app.dependency_overrides[provide_object_storage] = lambda: Mock(
        create_download_url=lambda key: f"https://signed.example/{key}",
    )
    yield
    client.app.dependency_overrides.pop(provide_object_storage, None)


def test_clerk_can_view_found_item_detail(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
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
                custody_location="Clerk Office",
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
    assert data["custody_location"] == "Clerk Office"
    assert data["status"] == "pending"

def test_administrative_can_approve_found_item(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
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
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
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
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
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
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
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


def test_administrative_can_reject_found_item(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_item():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND005",
                report_type=LostType.FOUND,
                item_category="Accessories",
                item_name="Watch",
                description="Black watch",
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
        f"/api/v1/lost-found/found-items/{item_id}/reject",
        headers=headers,
        json={
            "reason": "Invalid found-item report",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"

    async def get_rejected_item():
        async with session_factory() as session:
            return await session.get(LostItem, item_id)

    rejected_item = asyncio.run(get_rejected_item())

    assert rejected_item.status == LostStatus.REJECTED
    assert rejected_item.review_note == "Invalid found-item report"
    assert rejected_item.reviewed_by is not None


def test_rejection_reason_is_required(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_item():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND006",
                report_type=LostType.FOUND,
                item_category="Accessories",
                item_name="Bag",
                description="Black bag",
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

    response = client.post(
        f"/api/v1/lost-found/found-items/{item_id}/reject",
        headers=headers,
        json={
            "reason": "",
        },
    )

    assert response.status_code == 422

    async def get_item():
        async with session_factory() as session:
            return await session.get(LostItem, item_id)

    item = asyncio.run(get_item())

    assert item.status == LostStatus.PENDING
    assert item.review_note is None


def test_rejected_found_item_is_removed_from_pending_list(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_item():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND007",
                report_type=LostType.FOUND,
                item_category="Accessories",
                item_name="Umbrella",
                description="Black umbrella",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building C",
                custody_location="Administrative Office",
                reporter_email="user@example.com",
                status=LostStatus.PENDING,
            )

            session.add(item)
            await session.commit()
            await session.refresh(item)

            return item.id

    item_id = asyncio.run(seed_item())

    # Reject the found-item report
    reject_response = client.post(
        f"/api/v1/lost-found/found-items/{item_id}/reject",
        headers=headers,
        json={
            "reason": "Invalid found-item report",
        },
    )

    assert reject_response.status_code == 200

    # Check the pending approval list
    pending_response = client.get(
        "/api/v1/lost-found/pending-found-items",
        headers=headers,
    )

    assert pending_response.status_code == 200

    pending_items = pending_response.json()

    assert all(
        item["id"] != str(item_id)
        for item in pending_items
    )


def test_administrative_can_view_pending_lost_items(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_item():
        async with session_factory() as session:
            item = LostItem(
                item_code="LOST002",
                report_type=LostType.LOST,
                item_category="Electronics",
                item_name="Lost Phone",
                description="Black phone",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Lobby",
                custody_location=None,
                reporter_email="guest@example.com",
                status=LostStatus.PENDING,
            )

            session.add(item)
            await session.commit()
            await session.refresh(item)

            return item.id

    item_id = asyncio.run(seed_item())

    response = client.get(
        "/api/v1/lost-found/pending-lost-items",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == str(item_id)
        for item in data
    )


def test_administrative_can_view_lost_item_detail(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_item():
        async with session_factory() as session:
            item = LostItem(
                item_code="LOST003",
                report_type=LostType.LOST,
                item_category="Electronics",
                item_name="Phone",
                description="Black phone",
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

    response = client.get(
        f"/api/v1/lost-found/lost-items/{item_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(item_id)
    assert data["item_code"] == "LOST003"
    assert data["report_type"] == "lost"
    assert data["item_category"] == "Electronics"
    assert data["item_name"] == "Phone"
    assert data["description"] == "Black phone"
    assert data["location_detail"] == "Building A"
    assert data["reporter_email"] == "user@example.com"
    assert data["status"] == "pending"


def test_administrative_can_approve_lost_item(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_item():
        async with session_factory() as session:
            item = LostItem(
                item_code="LOST004",
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
        f"/api/v1/lost-found/lost-items/{item_id}/approve",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(item_id)
    assert data["report_type"] == "lost"
    assert data["status"] == "approved"

    async def get_approved_item():
        async with session_factory() as session:
            return await session.get(LostItem, item_id)

    approved_item = asyncio.run(get_approved_item())

    assert approved_item.status == LostStatus.APPROVED
    assert approved_item.reviewed_by is not None


def test_approved_lost_item_is_removed_from_pending_list(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_item():
        async with session_factory() as session:
            item = LostItem(
                item_code="LOST005",
                report_type=LostType.LOST,
                item_category="Electronics",
                item_name="Laptop",
                description="Silver laptop",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building B",
                custody_location=None,
                reporter_email="user@example.com",
                status=LostStatus.PENDING,
            )

            session.add(item)
            await session.commit()
            await session.refresh(item)

            return item.id

    item_id = asyncio.run(seed_item())

    # Approve lost-item announcement
    approve_response = client.post(
        f"/api/v1/lost-found/lost-items/{item_id}/approve",
        headers=headers,
    )

    assert approve_response.status_code == 200

    # Approved item must be removed from pending list
    pending_response = client.get(
        "/api/v1/lost-found/pending-lost-items",
        headers=headers,
    )

    assert pending_response.status_code == 200

    pending_items = pending_response.json()

    assert all(
        item["id"] != str(item_id)
        for item in pending_items
    )


def test_approved_lost_item_is_published(test_context, public_list_storage):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_item():
        async with session_factory() as session:
            item = LostItem(
                item_code="LOST006",
                report_type=LostType.LOST,
                item_category="Accessories",
                item_name="Wallet",
                description="Brown wallet",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building C",
                custody_location=None,
                reporter_email="user@example.com",
                status=LostStatus.PENDING,
            )

            session.add(item)
            await session.commit()
            await session.refresh(item)

            return item.id

    item_id = asyncio.run(seed_item())

    # Approve lost-item announcement
    approve_response = client.post(
        f"/api/v1/lost-found/lost-items/{item_id}/approve",
        headers=headers,
    )

    assert approve_response.status_code == 200

    # Check public Lost & Found list
    public_response = client.get(
        "/api/v1/guest/lost-items",
    )

    assert public_response.status_code == 200

    data = public_response.json()

    assert any(
        item["id"] == str(item_id)
        for item in data["items"]
    )


def test_clerk_can_view_ownership_request_detail(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_claim():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND100",
                report_type=LostType.FOUND,
                item_category="Electronics",
                item_name="Phone",
                description="Black phone",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building A",
                custody_location="Clerk Office",
                reporter_email="finder@example.com",
                status=LostStatus.APPROVED,
            )

            session.add(item)
            await session.flush()

            claim = LostClaim(
                found_item_id=item.id,
                claimant_name="Test User",
                claimant_email="owner@example.com",
                proof_detail="มีรอยแตกที่มุมซ้ายและใช้เคสสีดำ",
            )

            session.add(claim)
            await session.commit()
            await session.refresh(claim)

            return claim.id

    claim_id = asyncio.run(seed_claim())

    response = client.get(
        f"/api/v1/lost-found/ownership-requests/{claim_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(claim_id)
    assert data["claimant_name"] == "Test User"
    assert data["claimant_email"] == "owner@example.com"
    assert data["proof_detail"] == "มีรอยแตกที่มุมซ้ายและใช้เคสสีดำ"

    assert data["item_code"] == "FOUND100"
    assert data["item_name"] == "Phone"
    assert data["item_category"] == "Electronics"
    assert data["custody_location"] == "Clerk Office"
    assert data["status"] == "pending"


def test_clerk_can_view_pending_ownership_requests(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_claim():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND101",
                report_type=LostType.FOUND,
                item_category="Accessories",
                item_name="Wallet",
                description="Brown wallet",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Lobby",
                custody_location="Clerk Office",
                reporter_email="finder@example.com",
                status=LostStatus.APPROVED,
            )

            session.add(item)
            await session.flush()

            claim = LostClaim(
                found_item_id=item.id,
                claimant_name="Owner Test",
                claimant_email="owner2@example.com",
                proof_detail="มีบัตรประชาชนอยู่ด้านใน",
            )

            session.add(claim)
            await session.commit()
            await session.refresh(claim)

            return claim.id

    claim_id = asyncio.run(seed_claim())

    response = client.get(
        "/api/v1/lost-found/ownership-requests",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        claim["id"] == str(claim_id)
        for claim in data
    )


def test_clerk_can_approve_ownership_request(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_claim():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND102",
                report_type=LostType.FOUND,
                item_category="Electronics",
                item_name="Tablet",
                description="Black tablet",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building A",
                custody_location="Clerk Office",
                reporter_email="finder@example.com",
                status=LostStatus.APPROVED,
            )

            session.add(item)
            await session.flush()

            claim = LostClaim(
                found_item_id=item.id,
                claimant_name="Owner User",
                claimant_email="owner3@example.com",
                proof_detail="มีสติกเกอร์สีแดงด้านหลังเครื่อง",
            )

            session.add(claim)
            await session.commit()
            await session.refresh(claim)

            return claim.id

    claim_id = asyncio.run(seed_claim())

    response = client.post(
        f"/api/v1/lost-found/ownership-requests/{claim_id}/approve",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(claim_id)
    assert data["status"] == "approved"

    async def get_claim():
        async with session_factory() as session:
            return await session.get(LostClaim, claim_id)

    claim = asyncio.run(get_claim())

    assert claim.status == ClaimStatus.APPROVED
    assert claim.reviewed_by is not None


def test_clerk_can_request_additional_ownership_information(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_claim():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND103",
                report_type=LostType.FOUND,
                item_category="Electronics",
                item_name="Phone",
                description="Black phone",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building A",
                custody_location="Clerk Office",
                reporter_email="finder@example.com",
                status=LostStatus.APPROVED,
            )

            session.add(item)
            await session.flush()

            claim = LostClaim(
                found_item_id=item.id,
                claimant_name="Owner Test",
                claimant_email="owner4@example.com",
                proof_detail="Black phone with cracked screen",
            )

            session.add(claim)
            await session.commit()
            await session.refresh(claim)

            return claim.id

    claim_id = asyncio.run(seed_claim())

    response = client.post(
        f"/api/v1/lost-found/ownership-requests/{claim_id}/request-additional-info",
        headers=headers,
        json={
            "message": "Please provide additional proof of ownership",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(claim_id)
    assert data["status"] == "additional_info_required"

    async def get_claim():
        async with session_factory() as session:
            return await session.get(LostClaim, claim_id)

    claim = asyncio.run(get_claim())

    assert claim.status == ClaimStatus.ADDITIONAL_INFO_REQUIRED
    assert claim.reviewed_by is not None
    assert claim.review_note == "Please provide additional proof of ownership"


def test_clerk_can_update_return_status_to_ready_for_pickup(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_claim():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND200",
                report_type=LostType.FOUND,
                item_category="Accessories",
                item_name="Bag",
                description="Black bag",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building A",
                custody_location="Clerk Office",
                reporter_email="finder@example.com",
                status=LostStatus.APPROVED,
            )

            session.add(item)
            await session.flush()

            claim = LostClaim(
                found_item_id=item.id,
                claimant_name="Owner User",
                claimant_email="owner@example.com",
                proof_detail="มีพวงกุญแจสีแดงติดอยู่",
                status=ClaimStatus.APPROVED,
                return_status=ReturnStatus.PENDING,
            )

            session.add(claim)
            await session.commit()
            await session.refresh(claim)

            return claim.id

    claim_id = asyncio.run(seed_claim())

    response = client.patch(
        f"/api/v1/lost-found/ownership-requests/{claim_id}/return-status",
        headers=headers,
        json={
            "return_status": "ready_for_pickup",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(claim_id)
    assert data["status"] == "approved"
    assert data["return_status"] == "ready_for_pickup"

    async def get_claim():
        async with session_factory() as session:
            return await session.get(LostClaim, claim_id)

    claim = asyncio.run(get_claim())

    assert claim.return_status == ReturnStatus.READY_FOR_PICKUP


def test_clerk_can_update_return_status_to_returned(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_claim():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND201",
                report_type=LostType.FOUND,
                item_category="Accessories",
                item_name="Wallet",
                description="Brown wallet",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building B",
                custody_location="Clerk Office",
                reporter_email="finder@example.com",
                status=LostStatus.APPROVED,
            )

            session.add(item)
            await session.flush()

            claim = LostClaim(
                found_item_id=item.id,
                claimant_name="Owner User",
                claimant_email="owner201@example.com",
                proof_detail="มีบัตรนักศึกษาอยู่ด้านใน",
                status=ClaimStatus.APPROVED,
                return_status=ReturnStatus.READY_FOR_PICKUP,
            )

            session.add(claim)
            await session.commit()
            await session.refresh(claim)

            return claim.id

    claim_id = asyncio.run(seed_claim())

    response = client.patch(
        f"/api/v1/lost-found/ownership-requests/{claim_id}/return-status",
        headers=headers,
        json={
            "return_status": "returned",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(claim_id)
    assert data["status"] == "completed"
    assert data["return_status"] == "returned"

    async def get_claim():
        async with session_factory() as session:
            return await session.get(LostClaim, claim_id)

    claim = asyncio.run(get_claim())

    assert claim.status == ClaimStatus.COMPLETED
    assert claim.return_status == ReturnStatus.RETURNED

    async def get_item_status():
        async with session_factory() as session:
            return (await session.get(LostItem, claim.found_item_id)).status

    # คืนของแล้วต้องเอาประกาศออกจากหน้า guest ด้วย
    assert asyncio.run(get_item_status()) == LostStatus.CLAIMED


def test_invalid_return_status_returns_422(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_claim():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND202",
                report_type=LostType.FOUND,
                item_category="Electronics",
                item_name="Phone",
                description="Black phone",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building A",
                custody_location="Clerk Office",
                reporter_email="finder@example.com",
                status=LostStatus.APPROVED,
            )

            session.add(item)
            await session.flush()

            claim = LostClaim(
                found_item_id=item.id,
                claimant_name="Owner User",
                claimant_email="owner202@example.com",
                proof_detail="มีรอยแตกที่มุมซ้าย",
                status=ClaimStatus.APPROVED,
                return_status=ReturnStatus.PENDING,
            )

            session.add(claim)
            await session.commit()
            await session.refresh(claim)

            return claim.id

    claim_id = asyncio.run(seed_claim())

    response = client.patch(
        f"/api/v1/lost-found/ownership-requests/{claim_id}/return-status",
        headers=headers,
        json={
            "return_status": "invalid_status",
        },
    )

    assert response.status_code == 422


def test_cannot_update_return_status_for_unapproved_claim(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_claim():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND203",
                report_type=LostType.FOUND,
                item_category="Accessories",
                item_name="Bag",
                description="Blue bag",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building C",
                custody_location="Clerk Office",
                reporter_email="finder@example.com",
                status=LostStatus.APPROVED,
            )

            session.add(item)
            await session.flush()

            claim = LostClaim(
                found_item_id=item.id,
                claimant_name="Owner User",
                claimant_email="owner203@example.com",
                proof_detail="มีพวงกุญแจรูปดาว",
                status=ClaimStatus.PENDING,
                return_status=None,
            )

            session.add(claim)
            await session.commit()
            await session.refresh(claim)

            return claim.id

    claim_id = asyncio.run(seed_claim())

    response = client.patch(
        f"/api/v1/lost-found/ownership-requests/{claim_id}/return-status",
        headers=headers,
        json={
            "return_status": "ready_for_pickup",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Approved ownership request not found"


def test_return_status_history_is_saved(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_claim():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND205",
                report_type=LostType.FOUND,
                item_category="Accessories",
                item_name="Bag",
                description="Black bag",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building A",
                custody_location="Clerk Office",
                reporter_email="finder@example.com",
                status=LostStatus.APPROVED,
            )

            session.add(item)
            await session.flush()

            claim = LostClaim(
                found_item_id=item.id,
                claimant_name="Owner User",
                claimant_email="owner205@example.com",
                proof_detail="มีพวงกุญแจสีแดง",
                status=ClaimStatus.APPROVED,
                return_status=ReturnStatus.PENDING,
            )

            session.add(claim)
            await session.commit()
            await session.refresh(claim)

            return claim.id

    claim_id = asyncio.run(seed_claim())

    response = client.patch(
        f"/api/v1/lost-found/ownership-requests/{claim_id}/return-status",
        headers=headers,
        json={
            "return_status": "ready_for_pickup",
        },
    )

    assert response.status_code == 200

    async def get_history():
        async with session_factory() as session:
            result = await session.scalars(
                select(LostClaimReturnStatusHistory).where(
                    LostClaimReturnStatusHistory.claim_id == claim_id
                )
            )
            return list(result)

    history = asyncio.run(get_history())

    assert len(history) == 1
    assert history[0].old_status == ReturnStatus.PENDING
    assert history[0].new_status == ReturnStatus.READY_FOR_PICKUP
    assert history[0].staff_id is not None


def test_administrative_can_reject_lost_item(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_item():
        async with session_factory() as session:
            item = LostItem(
                item_code="LOST007",
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
        f"/api/v1/lost-found/lost-items/{item_id}/reject",
        headers=headers,
        json={
            "reason": "Invalid lost-item announcement",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"

    async def get_item():
        async with session_factory() as session:
            return await session.get(LostItem, item_id)

    item = asyncio.run(get_item())

    assert item.status == LostStatus.REJECTED
    assert item.review_note == "Invalid lost-item announcement"
    assert item.reviewed_by is not None


def test_lost_item_rejection_reason_is_required(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_item():
        async with session_factory() as session:
            item = LostItem(
                item_code="LOST008",
                report_type=LostType.LOST,
                item_category="Accessories",
                item_name="Bag",
                description="Black bag",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building B",
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
        f"/api/v1/lost-found/lost-items/{item_id}/reject",
        headers=headers,
        json={
            "reason": "",
        },
    )

    assert response.status_code == 422

    async def get_item():
        async with session_factory() as session:
            return await session.get(LostItem, item_id)

    item = asyncio.run(get_item())

    assert item.status == LostStatus.PENDING
    assert item.review_note is None


def test_rejected_lost_item_is_not_published_and_removed_from_pending_list(
    test_context, public_list_storage,
):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_item():
        async with session_factory() as session:
            item = LostItem(
                item_code="LOST009",
                report_type=LostType.LOST,
                item_category="Accessories",
                item_name="Wallet",
                description="Black wallet",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building C",
                custody_location=None,
                reporter_email="user@example.com",
                status=LostStatus.PENDING,
            )

            session.add(item)
            await session.commit()
            await session.refresh(item)

            return item.id

    item_id = asyncio.run(seed_item())

    reject_response = client.post(
        f"/api/v1/lost-found/lost-items/{item_id}/reject",
        headers=headers,
        json={
            "reason": "Invalid announcement",
        },
    )

    assert reject_response.status_code == 200

    pending_response = client.get(
        "/api/v1/lost-found/pending-lost-items",
        headers=headers,
    )

    assert pending_response.status_code == 200

    pending_items = pending_response.json()

    assert all(
        item["id"] != str(item_id)
        for item in pending_items
    )

    public_response = client.get(
        "/api/v1/guest/lost-items",
    )

    assert public_response.status_code == 200

    public_items = public_response.json()["items"]

    assert all(
        item["id"] != str(item_id)
        for item in public_items
    )


def test_clerk_can_schedule_pickup(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_claim():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND300",
                report_type=LostType.FOUND,
                item_category="Accessories",
                item_name="Bag",
                description="Black bag",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building A",
                custody_location="Clerk Office",
                reporter_email="finder@example.com",
                status=LostStatus.APPROVED,
            )

            session.add(item)
            await session.flush()

            claim = LostClaim(
                found_item_id=item.id,
                claimant_name="Owner User",
                claimant_email="owner300@example.com",
                proof_detail="มีพวงกุญแจสีแดง",
                status=ClaimStatus.APPROVED,
                return_status=ReturnStatus.PENDING,
            )

            session.add(claim)
            await session.commit()
            await session.refresh(claim)

            return claim.id

    claim_id = asyncio.run(seed_claim())

    response = client.post(
        f"/api/v1/lost-found/ownership-requests/{claim_id}/schedule-pickup",
        headers=headers,
        json={
            "pickup_datetime": "2026-09-20T13:30:00",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "scheduled"
    assert data["pickup_datetime"] == "2026-09-20T13:30:00"

    async def get_claim():
        async with session_factory() as session:
            return await session.get(LostClaim, claim_id)

    claim = asyncio.run(get_claim())

    assert claim.status == ClaimStatus.SCHEDULED
    assert claim.pickup_datetime is not None


def test_schedule_pickup_requires_datetime(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_claim():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND301",
                report_type=LostType.FOUND,
                item_category="Accessories",
                item_name="Bag",
                description="Black bag",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building A",
                custody_location="Clerk Office",
                reporter_email="finder@example.com",
                status=LostStatus.APPROVED,
            )

            session.add(item)
            await session.flush()

            claim = LostClaim(
                found_item_id=item.id,
                claimant_name="Owner User",
                claimant_email="owner301@example.com",
                proof_detail="มีสายคล้องสีแดง",
                status=ClaimStatus.APPROVED,
                return_status=ReturnStatus.PENDING,
            )

            session.add(claim)
            await session.commit()
            await session.refresh(claim)

            return claim.id

    claim_id = asyncio.run(seed_claim())

    response = client.post(
        f"/api/v1/lost-found/ownership-requests/{claim_id}/schedule-pickup",
        headers=headers,
        json={},
    )

    assert response.status_code == 422

    async def get_claim():
        async with session_factory() as session:
            return await session.get(LostClaim, claim_id)

    claim = asyncio.run(get_claim())

    assert claim.status == ClaimStatus.APPROVED
    assert claim.pickup_datetime is None


def test_view_scheduled_pickup_details(test_context):
    client, session_factory = test_context

    seed_staff(
        session_factory,
        email="clerk@example.com",
        password="admin-password",
        role="clerk",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "clerk@example.com",
            "password": "admin-password",
        },
    )

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    async def seed_claim():
        async with session_factory() as session:
            item = LostItem(
                item_code="FOUND302",
                report_type=LostType.FOUND,
                item_category="Accessories",
                item_name="Bag",
                description="Black bag",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building A",
                custody_location="Clerk Office",
                reporter_email="finder@example.com",
                status=LostStatus.APPROVED,
            )

            session.add(item)
            await session.flush()

            claim = LostClaim(
                found_item_id=item.id,
                claimant_name="Owner User",
                claimant_email="owner302@example.com",
                proof_detail="มีป้ายชื่อด้านใน",
                status=ClaimStatus.SCHEDULED,
                return_status=ReturnStatus.PENDING,
                pickup_datetime=datetime(2026, 9, 20, 13, 30),
            )

            session.add(claim)
            await session.commit()
            await session.refresh(claim)

            return claim.id

    claim_id = asyncio.run(seed_claim())

    response = client.get(
        f"/api/v1/lost-found/ownership-requests/{claim_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "scheduled"
    assert data["pickup_datetime"] == "2026-09-20T13:30:00"


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


def _seed_item(session_factory, *, report_type, status, claim_status=None):
    async def seed():
        async with session_factory() as session:
            item = LostItem(
                item_code=f"{report_type.value.upper()}-{uuid4().hex[:8]}",
                report_type=report_type,
                item_category="Accessories",
                item_name="Wallet",
                description="Brown wallet",
                event_datetime=datetime.now(timezone.utc),
                location_id=None,
                location_detail="Building B",
                custody_location="Clerk Office" if report_type == LostType.FOUND else None,
                reporter_email="reporter@example.com",
                status=status,
            )
            session.add(item)
            await session.flush()
            if claim_status is not None:
                session.add(
                    LostClaim(
                        found_item_id=item.id,
                        claimant_name="Owner User",
                        claimant_email="owner@example.com",
                        proof_detail="มีบัตรนักศึกษาอยู่ด้านใน",
                        status=claim_status,
                    )
                )
            await session.commit()
            return item.id

    return asyncio.run(seed())


def _item_status(session_factory, item_id):
    async def read():
        async with session_factory() as session:
            return (await session.get(LostItem, item_id)).status

    return asyncio.run(read())


@pytest.mark.parametrize(
    ("report_type", "collection"),
    [(LostType.FOUND, "found-items"), (LostType.LOST, "lost-items")],
)
def test_clerk_close_removes_item_from_public_list(
    test_context, public_list_storage, report_type, collection
):
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    item_id = _seed_item(session_factory, report_type=report_type, status=LostStatus.APPROVED)

    response = client.post(f"/api/v1/lost-found/{collection}/{item_id}/close", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "closed"
    assert _item_status(session_factory, item_id) == LostStatus.CLOSED
    public_items = client.get(f"/api/v1/guest/{collection}").json()["items"]
    assert all(item["id"] != str(item_id) for item in public_items)


def test_clerk_cannot_close_pending_item(test_context):
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    item_id = _seed_item(session_factory, report_type=LostType.FOUND, status=LostStatus.PENDING)

    response = client.post(f"/api/v1/lost-found/found-items/{item_id}/close", headers=headers)

    assert response.status_code == 404
    assert _item_status(session_factory, item_id) == LostStatus.PENDING


def test_close_found_item_with_wrong_report_type_returns_404(test_context):
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    item_id = _seed_item(session_factory, report_type=LostType.LOST, status=LostStatus.APPROVED)

    response = client.post(f"/api/v1/lost-found/found-items/{item_id}/close", headers=headers)

    assert response.status_code == 404
    assert _item_status(session_factory, item_id) == LostStatus.APPROVED


@pytest.mark.parametrize(
    "claim_status",
    [ClaimStatus.PENDING, ClaimStatus.ADDITIONAL_INFO_REQUIRED, ClaimStatus.APPROVED, ClaimStatus.SCHEDULED],
)
def test_clerk_cannot_close_found_item_with_active_claim(test_context, claim_status):
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    item_id = _seed_item(
        session_factory,
        report_type=LostType.FOUND,
        status=LostStatus.APPROVED,
        claim_status=claim_status,
    )

    response = client.post(f"/api/v1/lost-found/found-items/{item_id}/close", headers=headers)

    assert response.status_code == 409
    assert _item_status(session_factory, item_id) == LostStatus.APPROVED


def test_clerk_can_close_found_item_after_claim_was_rejected(test_context):
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    item_id = _seed_item(
        session_factory,
        report_type=LostType.FOUND,
        status=LostStatus.APPROVED,
        claim_status=ClaimStatus.REJECTED,
    )

    response = client.post(f"/api/v1/lost-found/found-items/{item_id}/close", headers=headers)

    assert response.status_code == 200
    assert _item_status(session_factory, item_id) == LostStatus.CLOSED


def test_close_requires_clerk_login(test_context):
    client, session_factory = test_context
    item_id = _seed_item(session_factory, report_type=LostType.LOST, status=LostStatus.APPROVED)

    response = client.post(f"/api/v1/lost-found/lost-items/{item_id}/close")

    assert response.status_code == 401
    assert _item_status(session_factory, item_id) == LostStatus.APPROVED


@pytest.fixture
def staff_image_storage(test_context):
    """R2 ตัวปลอมสำหรับ endpoint staff ที่สร้าง signed URL ของรูป"""
    client, _ = test_context
    client.app.dependency_overrides[provide_optional_object_storage] = lambda: Mock(
        create_download_url=lambda key: f"https://signed.example/{key}",
    )
    yield
    client.app.dependency_overrides.pop(provide_optional_object_storage, None)


def _seed_image(session_factory, item_id, *, sort_order=0):
    async def seed():
        async with session_factory() as session:
            image = Image(
                lost_item_id=item_id,
                object_key=f"lost-found/{item_id}/{sort_order}.webp",
                content_type="image/webp",
                width=32,
                height=24,
                sort_order=sort_order,
            )
            session.add(image)
            await session.commit()
            return image.object_key

    return asyncio.run(seed())


@pytest.mark.parametrize(
    ("report_type", "collection"),
    [(LostType.FOUND, "found-items"), (LostType.LOST, "lost-items")],
)
def test_clerk_sees_images_of_pending_item_before_approval(
    test_context, staff_image_storage, report_type, collection
):
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    item_id = _seed_item(session_factory, report_type=report_type, status=LostStatus.PENDING)
    second_key = _seed_image(session_factory, item_id, sort_order=1)
    first_key = _seed_image(session_factory, item_id, sort_order=0)

    detail = client.get(f"/api/v1/lost-found/{collection}/{item_id}", headers=headers)
    pending = client.get(f"/api/v1/lost-found/pending-{collection}", headers=headers)

    assert detail.status_code == 200
    assert [image["url"] for image in detail.json()["images"]] == [
        f"https://signed.example/{first_key}",
        f"https://signed.example/{second_key}",
    ]
    assert pending.status_code == 200
    pending_item = next(item for item in pending.json() if item["id"] == str(item_id))
    assert pending_item["images"][0]["url"] == f"https://signed.example/{first_key}"


def test_item_without_images_returns_empty_list(test_context, staff_image_storage):
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    item_id = _seed_item(session_factory, report_type=LostType.FOUND, status=LostStatus.PENDING)

    response = client.get(f"/api/v1/lost-found/found-items/{item_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["images"] == []


def test_detail_still_works_when_image_storage_is_not_configured(test_context):
    client, session_factory = test_context
    client.app.dependency_overrides[provide_optional_object_storage] = lambda: None
    try:
        headers = _clerk_headers(client, session_factory)
        item_id = _seed_item(session_factory, report_type=LostType.FOUND, status=LostStatus.PENDING)
        _seed_image(session_factory, item_id)

        response = client.get(f"/api/v1/lost-found/found-items/{item_id}", headers=headers)
    finally:
        client.app.dependency_overrides.pop(provide_optional_object_storage, None)

    assert response.status_code == 200
    assert response.json()["images"] == []


def test_approve_response_does_not_lazy_load_item_images(test_context):
    """approve คืน schema เดียวกับ detail ต้องไม่ไปแตะ relationship LostItem.images"""
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    item_id = _seed_item(session_factory, report_type=LostType.FOUND, status=LostStatus.PENDING)
    _seed_image(session_factory, item_id)

    response = client.post(f"/api/v1/lost-found/found-items/{item_id}/approve", headers=headers)

    assert response.status_code == 200
    assert response.json()["images"] == []
