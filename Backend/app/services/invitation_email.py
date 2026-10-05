"""Email transport boundary for staff account mail (SMTP or an institutional relay)."""

import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings


class EmailDeliveryError(RuntimeError):
    """Email could not be handed to the configured SMTP server."""


async def send_email(*, recipient: str, subject: str, body: str) -> None:
    """Hand one plain-text message to the configured SMTP server."""
    if not settings.smtp_host:
        raise EmailDeliveryError("Email delivery is not configured")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.mail_from
    message["To"] = recipient
    message.set_content(body)

    def _send() -> None:
        connection_options = {
            "host": settings.smtp_host,
            "port": settings.smtp_port,
            "timeout": settings.smtp_timeout_seconds,
        }
        if settings.smtp_use_ssl:
            connection = smtplib.SMTP_SSL(
                **connection_options, context=ssl.create_default_context()
            )
        else:
            connection = smtplib.SMTP(**connection_options)
        with connection as client:
            if settings.smtp_use_starttls and not settings.smtp_use_ssl:
                client.starttls(context=ssl.create_default_context())
            if settings.smtp_username:
                client.login(settings.smtp_username, settings.smtp_password or "")
            client.send_message(message)

    try:
        await asyncio.to_thread(_send)
    except (OSError, smtplib.SMTPException) as exc:
        raise EmailDeliveryError("Email delivery failed") from exc


async def send_invitation_email(
    *, recipient: str, staff_identifier: str, activation_link: str
) -> None:
    """Send an invitation containing an identifier and activation link, never a password."""
    await send_email(
        recipient=recipient,
        subject="Set up your Building Service Management account",
        body=(
            "Your staff identifier is: "
            f"{staff_identifier}\n\nSet your password using this one-time link:\n"
            f"{activation_link}\n\n"
            "This link expires soon. If you did not expect this email, contact an administrator."
        ),
    )


async def send_password_reset_email(
    *, recipient: str, reset_link: str, expires_in_minutes: int
) -> None:
    """Send a one-time reset link; the current password keeps working until it is used."""
    await send_email(
        recipient=recipient,
        subject="Reset your Building Service Management password",
        body=(
            "We received a request to reset the password for this staff account.\n\n"
            f"Choose a new password using this one-time link:\n{reset_link}\n\n"
            f"The link expires in {expires_in_minutes} minutes. If you did not request a "
            "reset, you can ignore this email; your current password will keep working."
        ),
    )
