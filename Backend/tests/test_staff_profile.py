"""Admin profile edits persist without changing role/password or exposing old invitations."""

import asyncio
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest
from conftest import seed_staff
from sqlalchemy import select
from test_admin_staff import admin_headers

from app.models.invitation import StaffInvitation
from app.models.staff import Staff


def _stored(factory, staff_id):
    async def read():
        async with factory() as session:
            account = await session.get(Staff, staff_id)
            return {
                key: getattr(account, key)
                for key in (
                    "id",
                    "full_name",
                    "email",
                    "role",
                    "status",
                    "password_hash",
                    "updated_at",
                )
            }

    return asyncio.run(read())


def test_edit_name_email_persists_and_preserves_identity_and_password(test_context):
    client, factory = test_context
    headers = admin_headers(client, factory)
    staff = seed_staff(
        factory, email="tech@example.com", password="chosen-password", role="technician"
    )
    before = _stored(factory, staff.id)
    response = client.patch(
        f"/api/v1/staff/{staff.id}",
        headers=headers,
        json={"full_name": "  New   Technician  ", "email": " NEW.TECH@EXAMPLE.COM "},
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "New Technician"
    assert response.json()["email"] == "new.tech@example.com"
    assert "password_hash" not in response.json()
    assert "email_sent" not in response.json()
    after = _stored(factory, staff.id)
    for key in ("id", "role", "status", "password_hash"):
        assert after[key] == before[key]
    listed = client.get("/api/v1/staff", headers=headers).json()
    assert next(a for a in listed if a["id"] == str(staff.id))["full_name"] == "New Technician"
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"identifier": "tech@example.com", "password": "chosen-password"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"identifier": "new.tech@example.com", "password": "chosen-password"},
        ).status_code
        == 200
    )


@pytest.mark.parametrize(
    "changes", [{}, {"email": "TECH@EXAMPLE.COM"}, {"full_name": " Test  Staff "}]
)
def test_unchanged_patch_does_not_change_updated_at(test_context, changes):
    client, factory = test_context
    headers = admin_headers(client, factory)
    staff = seed_staff(factory, email="tech@example.com", password="password", role="technician")
    before = _stored(factory, staff.id)
    assert (
        client.patch(f"/api/v1/staff/{staff.id}", headers=headers, json=changes).status_code == 200
    )
    assert _stored(factory, staff.id) == before


@pytest.mark.parametrize(
    "changes",
    [
        {"role": "technician"},
        {"role": "admin"},
        {"status": "suspended"},
        {"password": "new-password"},
        {"zone": "2"},
        {"full_name": None},
        {"email": None},
        {"full_name": "   "},
        {"full_name": "a" * 151},
        {"email": "invalid"},
        {"email": "a" * 64 + "@" + ".".join(["b" * 63, "c" * 63, "d" * 62])},
    ],
)
def test_role_and_invalid_fields_are_rejected_atomically(test_context, changes):
    client, factory = test_context
    headers = admin_headers(client, factory)
    staff = seed_staff(factory, email="tech@example.com", password="password", role="technician")
    before = _stored(factory, staff.id)
    response = client.patch(
        f"/api/v1/staff/{staff.id}",
        headers=headers,
        json={"full_name": "Should not save", **changes},
    )
    assert response.status_code == 422
    assert _stored(factory, staff.id) == before


@pytest.mark.parametrize("status", ["active", "suspended"])
def test_duplicate_existing_email_is_rejected(test_context, status):
    client, factory = test_context
    headers = admin_headers(client, factory)
    seed_staff(factory, email="taken@example.com", password="password", role="clerk", status=status)
    staff = seed_staff(factory, email="tech@example.com", password="password", role="technician")
    before = _stored(factory, staff.id)
    response = client.patch(
        f"/api/v1/staff/{staff.id}",
        headers=headers,
        json={"email": "TAKEN@EXAMPLE.COM", "full_name": "Do not save"},
    )
    assert response.status_code == 409
    assert _stored(factory, staff.id) == before


@pytest.mark.parametrize("role", ["clerk", "technician", "housekeeper"])
def test_only_admin_can_edit_profiles(test_context, role):
    client, factory = test_context
    staff = seed_staff(factory, email="staff@example.com", password="password", role=role)
    url = f"/api/v1/staff/{staff.id}"
    assert client.patch(url, json={"full_name": "New"}).status_code == 401
    token = client.post(
        "/api/v1/auth/login", json={"identifier": staff.email, "password": "password"}
    ).json()["access_token"]
    assert (
        client.patch(
            url, headers={"Authorization": f"Bearer {token}"}, json={"full_name": "New"}
        ).status_code
        == 403
    )


def test_missing_deleted_and_suspended_targets(test_context):
    client, factory = test_context
    headers = admin_headers(client, factory)
    assert client.patch(f"/api/v1/staff/{uuid4()}", headers=headers, json={}).status_code == 404
    assert client.patch("/api/v1/staff/invalid", headers=headers, json={}).status_code == 422
    for status, expected in (("deleted", 404), ("suspended", 200)):
        staff = seed_staff(
            factory,
            email=f"{status}@example.com",
            password="password",
            role="technician",
            status=status,
        )
        response = client.patch(
            f"/api/v1/staff/{staff.id}", headers=headers, json={"full_name": "New"}
        )
        assert response.status_code == expected
        assert _stored(factory, staff.id)["status"].value == status


def test_email_change_invalidates_old_link_and_resend_uses_new_email(test_context, monkeypatch):
    client, factory = test_context
    headers = admin_headers(client, factory)
    sent = []

    async def fake_send(**kwargs):
        sent.append(kwargs)

    monkeypatch.setattr("app.services.invitations.send_invitation_email", fake_send)
    created = client.post(
        "/api/v1/staff",
        headers=headers,
        json={"email": "old@example.com", "full_name": "Staff", "role": "clerk"},
    )
    staff_id = created.json()["id"]
    old_token = parse_qs(urlparse(sent[-1]["activation_link"]).query)["token"][0]
    updated = client.patch(
        f"/api/v1/staff/{staff_id}", headers=headers, json={"email": "new@example.com"}
    )
    assert updated.status_code == 200
    assert len(sent) == 1  # A profile edit must not send email automatically.
    assert (
        client.post("/api/v1/auth/activation/validate", json={"token": old_token}).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/auth/activation", json={"token": old_token, "password": "Chosen-Pass1!"}
        ).status_code
        == 400
    )
    assert (
        client.post(f"/api/v1/staff/{staff_id}/resend-invitation", headers=headers).status_code
        == 200
    )
    assert sent[-1]["recipient"] == "new@example.com"
    new_token = parse_qs(urlparse(sent[-1]["activation_link"]).query)["token"][0]
    assert (
        client.post(
            "/api/v1/auth/activation", json={"token": new_token, "password": "Chosen-Pass1!"}
        ).status_code
        == 204
    )
    assert (
        client.post(f"/api/v1/staff/{staff_id}/resend-invitation", headers=headers).status_code
        == 409
    )


def test_failed_email_update_keeps_old_invitation_valid(test_context, monkeypatch):
    client, factory = test_context
    headers = admin_headers(client, factory)
    links = []

    async def fake_send(**kwargs):
        links.append(kwargs["activation_link"])

    monkeypatch.setattr("app.services.invitations.send_invitation_email", fake_send)
    created = client.post(
        "/api/v1/staff",
        headers=headers,
        json={"email": "old@example.com", "full_name": "Staff", "role": "clerk"},
    )
    token = parse_qs(urlparse(links[0]).query)["token"][0]
    response = client.patch(
        f"/api/v1/staff/{created.json()['id']}",
        headers=headers,
        json={"email": "admin@example.com"},
    )
    assert response.status_code == 409
    assert client.post("/api/v1/auth/activation/validate", json={"token": token}).status_code == 200


@pytest.mark.parametrize("status", ["suspended", "deleted"])
def test_inactive_accounts_cannot_resend_or_activate(test_context, monkeypatch, status):
    client, factory = test_context
    headers = admin_headers(client, factory)
    links = []

    async def fake_send(**kwargs):
        links.append(kwargs["activation_link"])

    monkeypatch.setattr("app.services.invitations.send_invitation_email", fake_send)
    created = client.post(
        "/api/v1/staff",
        headers=headers,
        json={"email": "old@example.com", "full_name": "Staff", "role": "clerk"},
    )
    from uuid import UUID

    from app.models.enums import AccountStatus

    async def suspend():
        async with factory() as session:
            staff = await session.get(Staff, UUID(created.json()["id"]))
            staff.status = AccountStatus(status)
            await session.commit()

    asyncio.run(suspend())
    token = parse_qs(urlparse(links[0]).query)["token"][0]
    assert client.post("/api/v1/auth/activation/validate", json={"token": token}).status_code == 400
    assert (
        client.post(
            "/api/v1/auth/activation", json={"token": token, "password": "Chosen-Pass1!"}
        ).status_code
        == 400
    )
    assert client.post(
        f"/api/v1/staff/{created.json()['id']}/resend-invitation", headers=headers
    ).status_code == (404 if status == "deleted" else 409)
    assert len(links) == 1

    async def not_consumed():
        async with factory() as session:
            invitation = await session.scalar(select(StaffInvitation))
            assert invitation.used_at is None

    asyncio.run(not_consumed())


def test_deleted_email_can_be_reused_without_restoring_old_account(test_context):
    from app.models.enums import AccountStatus
    client, factory = test_context
    headers = admin_headers(client, factory)
    old = seed_staff(factory, email="reuse@example.com", password="old-password", role="clerk", status="deleted")
    staff = seed_staff(factory, email="tech@example.com", password="password", role="technician")
    response = client.patch(f"/api/v1/staff/{staff.id}", headers=headers, json={"email": "reuse@example.com"})
    assert response.status_code == 200
    assert response.json()["email"] == "reuse@example.com"
    assert _stored(factory, old.id)["status"] == AccountStatus.DELETED
    assert _stored(factory, old.id)["email"].endswith("@deleted.invalid")
