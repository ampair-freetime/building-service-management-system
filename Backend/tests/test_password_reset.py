"""Acceptance tests for self-service staff password reset by email."""

import asyncio
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from conftest import seed_staff
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.password_reset import StaffPasswordReset
from app.services.invitation_email import EmailDeliveryError
from app.services.rate_limit import SlidingWindowRateLimiter

OLD_PASSWORD = "Old-Pass1!"
NEW_PASSWORD = "New-Pass2!"
EXPECTED_DETAIL = (
    "If this email belongs to an active staff account, a reset link will be sent shortly."
)

Context = tuple[TestClient, async_sessionmaker[AsyncSession]]


@pytest.fixture
def sent_links(monkeypatch) -> list[dict]:
    """Capture reset emails instead of talking to SMTP."""
    sent: list[dict] = []

    async def fake_send(**kwargs) -> None:
        sent.append(kwargs)

    monkeypatch.setattr("app.services.password_reset.send_password_reset_email", fake_send)
    return sent


def _token(link: str) -> str:
    return parse_qs(urlparse(link).query)["token"][0]


def _request(client: TestClient, email: str):
    return client.post("/api/v1/auth/password-reset-requests", json={"email": email})


def _confirm(client: TestClient, token: str, password: str = NEW_PASSWORD):
    return client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": password},
    )


def _login(client: TestClient, email: str, password: str):
    return client.post("/api/v1/auth/login", json={"identifier": email, "password": password})


def _resets(factory: async_sessionmaker[AsyncSession]) -> list[StaffPasswordReset]:
    async def load() -> list[StaffPasswordReset]:
        async with factory() as session:
            rows = await session.scalars(
                select(StaffPasswordReset).order_by(StaffPasswordReset.created_at)
            )
            return list(rows)

    return asyncio.run(load())


def _age_resets(factory: async_sessionmaker[AsyncSession], **delta: float) -> None:
    """Move every reset row into the past to simulate cooldown or expiry."""

    async def shift() -> None:
        async with factory() as session:
            past = datetime.now(UTC) - timedelta(**delta)
            await session.execute(
                update(StaffPasswordReset).values(created_at=past, expires_at=past)
            )
            await session.commit()

    asyncio.run(shift())


def _admin_headers(client: TestClient, factory) -> dict[str, str]:
    seed_staff(factory, email="admin@example.com", password=OLD_PASSWORD, role="admin")
    token = _login(client, "admin@example.com", OLD_PASSWORD).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_full_reset_flow_changes_password_once(test_context: Context, sent_links) -> None:
    client, factory = test_context
    seed_staff(factory, email="tech@example.com", password=OLD_PASSWORD, role="technician")

    response = _request(client, " Tech@Example.com ")
    assert response.status_code == 202
    assert response.json() == {"detail": EXPECTED_DETAIL}
    assert len(sent_links) == 1
    link = sent_links[0]["reset_link"]
    assert sent_links[0]["recipient"] == "tech@example.com"
    # The address must not leak through the URL; only the token is in the query.
    assert "tech%40example.com" not in link and "tech@example.com" not in link
    assert link.startswith("http://localhost:5173/staff/reset-password?token=")
    token = _token(link)

    [row] = _resets(factory)
    assert row.token_hash != token and len(row.token_hash) == 64
    assert row.delivery_status == "sent"

    assert (
        client.post("/api/v1/auth/password-reset/validate", json={"token": token}).status_code
        == 200
    )
    assert _confirm(client, token).status_code == 204
    assert _login(client, "tech@example.com", NEW_PASSWORD).status_code == 200
    assert _login(client, "tech@example.com", OLD_PASSWORD).status_code == 401

    reused = _confirm(client, token, "Other-Pass3!")
    assert reused.status_code == 400
    assert "Request a new one" in reused.json()["detail"]
    assert (
        client.post("/api/v1/auth/password-reset/validate", json={"token": token}).status_code
        == 400
    )


def test_request_response_is_identical_for_every_account_state(
    test_context: Context, sent_links
) -> None:
    client, factory = test_context
    seed_staff(factory, email="active@example.com", password=OLD_PASSWORD, role="clerk")
    seed_staff(
        factory, email="suspended@example.com", password=OLD_PASSWORD, role="clerk",
        status="suspended",
    )
    seed_staff(
        factory, email="deleted@example.com", password=OLD_PASSWORD, role="clerk",
        status="deleted",
    )
    seed_staff(
        factory, email="pending@example.com", password=OLD_PASSWORD, role="clerk",
        activated=False,
    )

    responses = [
        _request(client, email)
        for email in (
            "active@example.com",
            "unknown@example.com",
            "suspended@example.com",
            "deleted@example.com",
            "pending@example.com",
        )
    ]
    assert {(r.status_code, r.text) for r in responses} == {
        (202, '{"detail":"' + EXPECTED_DETAIL + '"}')
    }
    assert [mail["recipient"] for mail in sent_links] == ["active@example.com"]


def test_reset_logs_out_existing_sessions(test_context: Context, sent_links) -> None:
    client, factory = test_context
    seed_staff(factory, email="tech@example.com", password=OLD_PASSWORD, role="technician")
    old_jwt = _login(client, "tech@example.com", OLD_PASSWORD).json()["access_token"]
    old_headers = {"Authorization": f"Bearer {old_jwt}"}
    assert client.get("/api/v1/auth/me", headers=old_headers).status_code == 200

    _request(client, "tech@example.com")
    assert _confirm(client, _token(sent_links[0]["reset_link"])).status_code == 204

    assert client.get("/api/v1/auth/me", headers=old_headers).status_code == 401
    new_jwt = _login(client, "tech@example.com", NEW_PASSWORD).json()["access_token"]
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_jwt}"}).status_code
        == 200
    )


def test_cooldown_then_new_link_supersedes_old_one(test_context: Context, sent_links) -> None:
    client, factory = test_context
    seed_staff(factory, email="tech@example.com", password=OLD_PASSWORD, role="technician")

    _request(client, "tech@example.com")
    _request(client, "tech@example.com")  # within cooldown: no second row, no second mail
    assert len(sent_links) == 1 and len(_resets(factory)) == 1
    old_token = _token(sent_links[0]["reset_link"])

    async def end_cooldown() -> None:
        async with factory() as session:
            await session.execute(
                update(StaffPasswordReset).values(
                    created_at=datetime.now(UTC) - timedelta(minutes=5)
                )
            )
            await session.commit()

    asyncio.run(end_cooldown())
    _request(client, "tech@example.com")
    assert len(sent_links) == 2
    assert _confirm(client, old_token).status_code == 400
    assert _confirm(client, _token(sent_links[1]["reset_link"])).status_code == 204


def test_expired_link_is_rejected(test_context: Context, sent_links) -> None:
    client, factory = test_context
    seed_staff(factory, email="tech@example.com", password=OLD_PASSWORD, role="technician")
    _request(client, "tech@example.com")
    token = _token(sent_links[0]["reset_link"])
    _age_resets(factory, minutes=1)

    assert (
        client.post("/api/v1/auth/password-reset/validate", json={"token": token}).status_code
        == 400
    )
    assert _confirm(client, token).status_code == 400
    assert _login(client, "tech@example.com", OLD_PASSWORD).status_code == 200


def test_email_change_and_deletion_invalidate_links(test_context: Context, sent_links) -> None:
    client, factory = test_context
    headers = _admin_headers(client, factory)
    moved = seed_staff(factory, email="moved@example.com", password=OLD_PASSWORD, role="clerk")
    removed = seed_staff(
        factory, email="removed@example.com", password=OLD_PASSWORD, role="clerk"
    )
    _request(client, "moved@example.com")
    _request(client, "removed@example.com")
    moved_token, removed_token = (_token(mail["reset_link"]) for mail in sent_links)

    assert (
        client.patch(
            f"/api/v1/staff/{moved.id}", headers=headers, json={"email": "new@example.com"}
        ).status_code
        == 200
    )
    assert client.delete(f"/api/v1/staff/{removed.id}", headers=headers).status_code == 204

    assert _confirm(client, moved_token).status_code == 400
    assert _confirm(client, removed_token).status_code == 400
    assert {row.invalidated_at is not None for row in _resets(factory)} == {True}


def test_smtp_failure_still_answers_202(test_context: Context, monkeypatch) -> None:
    client, factory = test_context
    seed_staff(factory, email="tech@example.com", password=OLD_PASSWORD, role="technician")

    async def failing_send(**kwargs) -> None:
        raise EmailDeliveryError("Email delivery failed")

    monkeypatch.setattr("app.services.password_reset.send_password_reset_email", failing_send)
    response = _request(client, "tech@example.com")
    assert response.status_code == 202
    assert response.json() == {"detail": EXPECTED_DETAIL}
    [row] = _resets(factory)
    assert row.delivery_status == "failed" and row.sent_at is None


def test_weak_password_is_rejected_and_link_stays_usable(
    test_context: Context, sent_links
) -> None:
    client, factory = test_context
    seed_staff(factory, email="tech@example.com", password=OLD_PASSWORD, role="technician")
    _request(client, "tech@example.com")
    token = _token(sent_links[0]["reset_link"])

    for weak in ("short1!", "alllowercase1!", "ALLUPPERCASE1!", "NoDigits!!", "NoSpecial12"):
        assert _confirm(client, token, weak).status_code == 422
    assert _confirm(client, token).status_code == 204


def test_ip_rate_limit_answers_202_without_sending(test_context: Context, sent_links) -> None:
    client, factory = test_context
    client.app.state.password_reset_limiter = SlidingWindowRateLimiter(
        limit=2, window_seconds=900
    )
    for index in range(3):
        seed_staff(factory, email=f"user{index}@example.com", password=OLD_PASSWORD, role="clerk")

    responses = [_request(client, f"user{index}@example.com") for index in range(3)]
    assert [r.status_code for r in responses] == [202, 202, 202]
    assert [mail["recipient"] for mail in sent_links] == [
        "user0@example.com",
        "user1@example.com",
    ]


def test_activation_uses_the_same_password_rule(test_context: Context, monkeypatch) -> None:
    client, factory = test_context
    links: list[str] = []

    async def fake_invite(**kwargs) -> None:
        links.append(kwargs["activation_link"])

    monkeypatch.setattr("app.services.invitations.send_invitation_email", fake_invite)
    headers = _admin_headers(client, factory)
    client.post(
        "/api/v1/staff",
        headers=headers,
        json={"email": "fresh@example.com", "full_name": "Fresh", "role": "clerk"},
    )
    token = _token(links[0])
    weak = client.post("/api/v1/auth/activation", json={"token": token, "password": "weakpass"})
    assert weak.status_code == 422
    strong = client.post("/api/v1/auth/activation", json={"token": token, "password": NEW_PASSWORD})
    assert strong.status_code == 204
