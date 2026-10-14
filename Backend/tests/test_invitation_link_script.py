"""scripts/invitation_link.py: a working link even when invitation email cannot be sent."""

import asyncio
from urllib.parse import parse_qs, urlsplit

from conftest import seed_staff

from scripts import invitation_link


def test_prints_working_link_without_smtp(test_context, capsys):
    client, factory = test_context
    seed_staff(factory, email="new@example.com", password="x", role="clerk", activated=False)

    assert asyncio.run(invitation_link.issue_link(factory, "NEW@example.com")) == 0
    output = capsys.readouterr().out
    assert "could not be sent" in output
    link = next(line for line in output.splitlines() if line.startswith("http"))
    token = parse_qs(urlsplit(link).query)["token"][0]

    activated = client.post(
        "/api/v1/auth/activation", json={"token": token, "password": "Brand-New-Pass1"}
    )
    assert activated.status_code == 204
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "new@example.com", "password": "Brand-New-Pass1"},
    )
    assert login.status_code == 200


def test_refuses_activated_or_unknown_accounts(test_context, capsys):
    _, factory = test_context
    seed_staff(factory, email="done@example.com", password="x", role="clerk")

    assert asyncio.run(invitation_link.issue_link(factory, "done@example.com")) == 1
    assert "already been activated" in capsys.readouterr().out
    assert asyncio.run(invitation_link.issue_link(factory, "nobody@example.com")) == 1
    assert "No staff account" in capsys.readouterr().out
