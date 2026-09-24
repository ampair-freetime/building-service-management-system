"""ตรวจ flow สร้าง Staff โดย Admin และการส่งรหัสผ่านเริ่มต้น."""

import re
import string

from conftest import seed_staff
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import generate_temporary_password
from app.services.email import EmailDeliveryError


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


def test_create_sends_password_that_can_log_in(test_context, monkeypatch) -> None:
    client, session_factory = test_context
    headers = admin_headers(client, session_factory)
    sent: list[dict[str, str]] = []
    monkeypatch.setattr("app.services.staff.send_email", lambda **kwargs: sent.append(kwargs))

    response = client.post("/api/v1/staff", headers=headers, json=staff_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["email_sent"] is True
    assert body["status"] == "active"
    assert body["email"] == "hk@example.com"
    assert "staff_code" not in body
    assert len(sent) == 1
    assert sent[0]["to"] == "hk@example.com"
    assert "hk@example.com" in sent[0]["text_body"]
    assert "รหัสพนักงาน" not in sent[0]["text_body"]
    password = re.search(r"รหัสผ่านเริ่มต้น: (.+)", sent[0]["text_body"]).group(1)
    assert "password" not in body
    assert "password_hash" not in body
    assert password not in response.text

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "hk@example.com", "password": password},
    )
    assert login.status_code == 200
    assert login.json()["staff"]["id"] == body["id"]


def test_delivery_failure_keeps_account_and_reports_false(test_context, monkeypatch) -> None:
    client, session_factory = test_context
    headers = admin_headers(client, session_factory)

    def fail_delivery(**kwargs) -> None:
        raise EmailDeliveryError("SMTP unavailable")

    monkeypatch.setattr("app.services.staff.send_email", fail_delivery)
    response = client.post("/api/v1/staff", headers=headers, json=staff_payload())

    assert response.status_code == 201
    assert response.json()["email_sent"] is False
    listing = client.get("/api/v1/staff", headers=headers)
    assert [item["email"] for item in listing.json()] == ["admin@example.com", "hk@example.com"]


def test_duplicate_or_invalid_request_never_sends_email(test_context, monkeypatch) -> None:
    client, session_factory = test_context
    headers = admin_headers(client, session_factory)
    sent: list[dict[str, str]] = []
    monkeypatch.setattr("app.services.staff.send_email", lambda **kwargs: sent.append(kwargs))
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
    monkeypatch.setattr("app.services.staff.send_email", lambda **kwargs: sent.append(kwargs))
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


def test_temporary_password_has_all_character_types() -> None:
    passwords = [generate_temporary_password() for _ in range(100)]
    assert len(set(passwords)) == len(passwords)
    for password in passwords:
        assert len(password) == 12
        assert any(char.isupper() for char in password)
        assert any(char.islower() for char in password)
        assert any(char.isdigit() for char in password)
        assert any(char in "@#$%!?" for char in password)
        assert not set(password) & set("0Oo1lI")
        assert set(password) <= set(string.ascii_letters + string.digits + "@#$%!?")
