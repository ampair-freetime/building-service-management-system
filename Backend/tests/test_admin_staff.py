"""ตรวจ flow สร้าง Staff โดย Admin และการส่ง invitation ที่ปลอดภัย."""

from conftest import seed_staff
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.invitation_email import EmailDeliveryError


def admin_headers(
    client: TestClient, session_factory: async_sessionmaker[AsyncSession]
) -> dict[str, str]:
    seed_staff(
        session_factory,
        email="admin@example.com",
        password="admin-password",
        role="admin",
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin@example.com", "password": "admin-password"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def staff_payload(**changes: str) -> dict[str, str]:
    payload = {
        "email": "HK@EXAMPLE.COM",
        "full_name": "House Keeper",
        "role": "housekeeper",
    }
    payload.update(changes)
    return payload


def test_create_sends_invitation_without_exposing_password(test_context, monkeypatch) -> None:
    client, session_factory = test_context
    headers = admin_headers(client, session_factory)
    sent: list[dict[str, str]] = []
    async def send_invitation(**kwargs) -> None:
        sent.append(kwargs)

    monkeypatch.setattr("app.services.invitations.send_invitation_email", send_invitation)

    response = client.post("/api/v1/staff", headers=headers, json=staff_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["email_sent"] is True
    assert body["status"] == "active"
    assert body["email"] == "hk@example.com"
    assert "staff_code" not in body
    assert len(sent) == 1
    assert sent[0]["recipient"] == "hk@example.com"
    assert sent[0]["staff_identifier"] == "hk@example.com"
    assert "token=" in sent[0]["activation_link"]
    assert "password" not in body
    assert "password_hash" not in body
    assert "token=" not in response.text


def test_delivery_failure_keeps_account_and_reports_false(test_context, monkeypatch) -> None:
    client, session_factory = test_context
    headers = admin_headers(client, session_factory)

    async def fail_delivery(**kwargs) -> None:
        raise EmailDeliveryError("SMTP unavailable")

    monkeypatch.setattr("app.services.invitations.send_invitation_email", fail_delivery)
    response = client.post("/api/v1/staff", headers=headers, json=staff_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["email_sent"] is False
    assert "temporary_password" not in body
    listing = client.get("/api/v1/staff", headers=headers)
    assert [item["email"] for item in listing.json()] == ["admin@example.com", "hk@example.com"]


def test_duplicate_or_invalid_request_never_sends_email(test_context, monkeypatch) -> None:
    client, session_factory = test_context
    headers = admin_headers(client, session_factory)
    sent: list[dict[str, str]] = []
    async def send_invitation(**kwargs) -> None:
        sent.append(kwargs)

    monkeypatch.setattr("app.services.invitations.send_invitation_email", send_invitation)
    first = client.post("/api/v1/staff", headers=headers, json=staff_payload())
    assert first.status_code == 201
    assert len(sent) == 1

    duplicate = client.post(
        "/api/v1/staff",
        headers=headers,
        json=staff_payload(email="hk@example.com"),
    )
    assert duplicate.status_code == 409
    assert len(sent) == 1

    for extra in ({"password": "not-allowed"}, {"status": "suspended"}, {"staff_code": "HK002"}):
        invalid = client.post("/api/v1/staff", headers=headers, json={**staff_payload(), **extra})
        assert invalid.status_code == 422
    assert len(sent) == 1

    blank_name = client.post(
        "/api/v1/staff", headers=headers, json=staff_payload(email="blank@example.com", full_name="   ")
    )
    assert blank_name.status_code == 422
    assert len(sent) == 1


def test_only_admin_can_create_staff(test_context, monkeypatch) -> None:
    client, session_factory = test_context
    sent: list[dict[str, str]] = []
    async def send_invitation(**kwargs) -> None:
        sent.append(kwargs)

    monkeypatch.setattr("app.services.invitations.send_invitation_email", send_invitation)
    seed_staff(
        session_factory,
        email="tech@example.com",
        password="tech-password",
        role="technician",
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "tech@example.com", "password": "tech-password"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.post("/api/v1/staff", json=staff_payload()).status_code == 401
    assert client.post("/api/v1/staff", headers=headers, json=staff_payload()).status_code == 403
    assert sent == []
