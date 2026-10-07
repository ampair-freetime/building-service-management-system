"""Email transport boundary for staff account mail (SMTP or an institutional relay)."""

import asyncio
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

from app.core.config import settings


class EmailDeliveryError(RuntimeError):
    """Email could not be handed to the configured SMTP server."""


async def send_email(*, recipient: str, subject: str, body: str) -> None:
    """Hand one plain-text message to the configured SMTP server."""
    if not settings.smtp_host:
        raise EmailDeliveryError("Email delivery is not configured")

    message = EmailMessage()
    message["Subject"] = subject
    sender = settings.mail_from.strip()
    # Accept legacy "Display Name address@example.com" configuration.
    if "<" not in sender and " " in sender:
        name, address = sender.rsplit(" ", 1)
        if "@" in address:
            sender = formataddr((name, address))
    message["From"] = sender
    message["Date"] = formatdate(localtime=False)
    message["Message-ID"] = make_msgid()
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
        subject="ตั้งรหัสผ่านบัญชีเจ้าหน้าที่ · CS Building Care",
        body=(
            "คุณได้รับเชิญให้ใช้งานระบบ CS Building Care ในฐานะเจ้าหน้าที่\n\n"
            f"อีเมลสำหรับเข้าสู่ระบบ: {staff_identifier}\n"
            "กรุณาเปิดลิงก์ด้านล่างเพื่อตั้งรหัสผ่านและเปิดใช้งานบัญชี:\n"
            f"{activation_link}\n\n"
            "ลิงก์นี้ใช้ได้ครั้งเดียว โปรดตั้งรหัสผ่านก่อนลิงก์หมดอายุ\n"
            "หากลิงก์หมดอายุ กรุณาติดต่อผู้ดูแลระบบเพื่อส่งคำเชิญใหม่\n"
            "หากไม่ทราบที่มาของคำเชิญนี้ กรุณาติดต่อผู้ดูแลระบบ\n\n"

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
