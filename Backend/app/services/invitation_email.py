"""SMTP delivery for staff invitations."""

import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings


class EmailDeliveryError(RuntimeError):
    """Email could not be handed to the configured SMTP server."""


async def send_invitation_email(
    *, recipient: str, staff_identifier: str, activation_link: str
) -> None:
    """Send an invitation containing an identifier and activation link, never a password."""
    if not settings.smtp_host:
        raise EmailDeliveryError("Invitation email is not configured")

    message = EmailMessage()
    message["Subject"] = "Set up your Building Service Management account"
    message["From"] = settings.mail_from
    message["To"] = recipient
    message.set_content(
        "Your staff identifier is: "
        f"{staff_identifier}\n\nSet your password using this one-time link:\n{activation_link}\n\n"
        "This link expires soon. If you did not expect this email, contact an administrator."
    )

    def _send() -> None:
        with smtplib.SMTP(
            settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds
        ) as client:
            if settings.smtp_use_starttls:
                client.starttls(context=ssl.create_default_context())
            if settings.smtp_username:
                client.login(settings.smtp_username, settings.smtp_password or "")
            client.send_message(message)

    try:
        await asyncio.to_thread(_send)
    except (OSError, smtplib.SMTPException) as exc:
        raise EmailDeliveryError("Invitation email delivery failed") from exc
