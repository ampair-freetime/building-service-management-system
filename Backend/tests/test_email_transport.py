"""Exercise the actual adapter with fake sockets; never send external email."""

import asyncio
import smtplib
import ssl

import pytest

from app.core.config import Settings
from app.services import invitation_email


@pytest.mark.parametrize("implicit_ssl", [False, True])
def test_smtp_tls_mode_and_message(implicit_ssl, monkeypatch):
    calls = []
    configuration = Settings(
        _env_file=None,
        smtp_host="relay.example.org",
        smtp_port=465 if implicit_ssl else 587,
        smtp_use_ssl=implicit_ssl,
        smtp_use_starttls=not implicit_ssl,
        smtp_username="user",
        smtp_password="test-password",
        smtp_timeout_seconds=4,
        mail_from="Care <care@example.org>",
    )
    monkeypatch.setattr(invitation_email, "settings", configuration)

    class Connection:
        def __init__(self, **options):
            calls.append(("connect", options))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def starttls(self, *, context):
            assert context.check_hostname
            assert context.verify_mode == ssl.CERT_REQUIRED
            calls.append(("starttls", None))

        def login(self, user, password):
            assert (user, password) == ("user", "test-password")
            calls.append(("login", None))

        def send_message(self, message):
            assert message["To"] == "staff@example.org"
            assert (
                "https://care.example.org/staff/setup-password?token=test" in message.get_content()
            )
            calls.append(("send", None))

    def unexpected_connection(**kwargs):
        pytest.fail("Wrong SMTP TLS mode selected")

    monkeypatch.setattr(
        invitation_email.smtplib, "SMTP_SSL", Connection if implicit_ssl else unexpected_connection
    )
    monkeypatch.setattr(
        invitation_email.smtplib, "SMTP", unexpected_connection if implicit_ssl else Connection
    )
    asyncio.run(
        invitation_email.send_invitation_email(
            recipient="staff@example.org",
            staff_identifier="staff@example.org",
            activation_link="https://care.example.org/staff/setup-password?token=test",
        )
    )
    assert calls[0][1]["timeout"] == 4
    assert calls[0][1]["port"] == (465 if implicit_ssl else 587)
    if implicit_ssl:
        assert calls[0][1]["context"].verify_mode == ssl.CERT_REQUIRED
    assert [c[0] for c in calls] == (
        ["connect", "login", "send"] if implicit_ssl else ["connect", "starttls", "login", "send"]
    )


@pytest.mark.parametrize(
    "failure", [TimeoutError(), smtplib.SMTPAuthenticationError(535, b"Denied")]
)
def test_transport_failure_uses_existing_business_error(monkeypatch, failure):
    monkeypatch.setattr(
        invitation_email,
        "settings",
        Settings(
            _env_file=None,
            smtp_host="relay.example.org",
        ),
    )

    def fail(**kwargs):
        raise failure

    monkeypatch.setattr(invitation_email.smtplib, "SMTP", fail)
    with pytest.raises(invitation_email.EmailDeliveryError, match="delivery failed"):
        asyncio.run(
            invitation_email.send_invitation_email(
                recipient="staff@example.org",
                staff_identifier="staff@example.org",
                activation_link="https://care.example.org/staff/setup-password?token=test",
            )
        )
