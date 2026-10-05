"""Acceptance tests for secure staff account invitations."""

from urllib.parse import parse_qs, urlparse

from conftest import seed_staff
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def _admin_headers(
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
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _token_from_link(link: str) -> str:
    return parse_qs(urlparse(link).query)["token"][0]


def test_create_invitation_activate_once_and_never_expose_password(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]], monkeypatch
) -> None:
    client, session_factory = test_context
    sent_links: list[str] = []

    async def fake_send(**kwargs: str) -> None:
        assert kwargs["staff_identifier"] == "new.tech@example.com"
        assert "password" not in kwargs
        sent_links.append(kwargs["activation_link"])

    monkeypatch.setattr("app.services.invitations.send_invitation_email", fake_send)
    headers = _admin_headers(client, session_factory)
    response = client.post(
        "/api/v1/staff",
        headers=headers,
        json={
            "email": "new.tech@example.com",
            "full_name": "New Technician",
            "role": "technician",
        },
    )

    assert response.status_code == 201
    assert response.json()["email_sent"] is True
    assert response.json()["email"] == "new.tech@example.com"
    assert "password" not in response.text
    assert len(sent_links) == 1
    token = _token_from_link(sent_links[0])

    assert (
        client.post("/api/v1/auth/activation/validate", json={"token": token}).status_code
        == 200
    )
    activated = client.post(
        "/api/v1/auth/setup-password",
        json={"token": token, "password": "Chosen-Pass1!"},
    )
    assert activated.status_code == 204
    reused = client.post(
        "/api/v1/auth/setup-password",
        json={"token": token, "password": "Another-Pass2!"},
    )
    assert reused.status_code == 400
    assert "Request a new invitation" in reused.json()["detail"]

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "new.tech@example.com", "password": "Chosen-Pass1!"},
    )
    assert login.status_code == 200


def test_resend_invalidates_previous_link_and_keeps_same_staff_account(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]], monkeypatch
) -> None:
    client, session_factory = test_context
    sent_links: list[str] = []

    async def fake_send(**kwargs: str) -> None:
        sent_links.append(kwargs["activation_link"])

    monkeypatch.setattr("app.services.invitations.send_invitation_email", fake_send)
    headers = _admin_headers(client, session_factory)
    created = client.post(
        "/api/v1/staff",
        headers=headers,
        json={
            "email": "new.housekeeper@example.com",
            "full_name": "New Housekeeper",
            "role": "housekeeper",
        },
    )
    staff_id = created.json()["id"]
    first_token = _token_from_link(sent_links[-1])
    resent = client.post(f"/api/v1/staff/{staff_id}/resend-invitation", headers=headers)

    assert resent.status_code == 200
    assert resent.json()["id"] == staff_id
    assert len(sent_links) == 2
    assert client.post(
        "/api/v1/auth/activation/validate", json={"token": first_token}
    ).status_code == 400
    assert (
        client.post(
            "/api/v1/auth/activation/validate",
            json={"token": _token_from_link(sent_links[-1])},
        ).status_code
        == 200
    )


def test_delivery_failure_creates_account_and_can_be_retried(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]], monkeypatch
) -> None:
    client, session_factory = test_context

    async def failed_send(**kwargs: str) -> None:
        from app.services.invitation_email import EmailDeliveryError

        raise EmailDeliveryError("provider unavailable")

    monkeypatch.setattr("app.services.invitations.send_invitation_email", failed_send)
    headers = _admin_headers(client, session_factory)
    created = client.post(
        "/api/v1/staff",
        headers=headers,
        json={
            "email": "new.clerk@example.com",
            "full_name": "New Clerk",
            "role": "clerk",
        },
    )
    assert created.status_code == 201
    assert created.json()["email_sent"] is False
    assert "provider unavailable" not in created.text

    async def delivered_send(**kwargs: str) -> None:
        return None

    monkeypatch.setattr("app.services.invitations.send_invitation_email", delivered_send)
    retried = client.post(
        f"/api/v1/staff/{created.json()['id']}/resend-invitation", headers=headers
    )
    assert retried.status_code == 200
    assert retried.json()["email_sent"] is True
