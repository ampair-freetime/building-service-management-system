"""สร้างและส่งอีเมลรหัสผ่านเริ่มต้นให้พนักงาน."""

import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings


class EmailDeliveryError(Exception):
    """SMTP ไม่พร้อมหรือส่งข้อความไม่สำเร็จ."""


def build_staff_welcome_email(
    *, full_name: str, staff_code: str, email: str, temporary_password: str
) -> tuple[str, str]:
    """คืนหัวข้อและเนื้อหาเมลที่พนักงานใช้เข้าสู่ระบบครั้งแรก."""
    subject = "ข้อมูลเข้าสู่ระบบ Building Care สำหรับพนักงาน"
    body = (
        f"สวัสดีคุณ {full_name}\n\n"
        "บัญชีพนักงานของคุณพร้อมใช้งานแล้ว\n"
        f"รหัสพนักงาน: {staff_code}\n"
        f"อีเมลที่ใช้เข้าสู่ระบบ: {email}\n"
        f"รหัสผ่านเริ่มต้น: {temporary_password}\n"
        f"หน้าเข้าสู่ระบบ: {settings.staff_login_url}\n\n"
        "กรุณาเปลี่ยนรหัสผ่านหลังเข้าสู่ระบบครั้งแรก\n"
        "หากคุณไม่ได้ขอบัญชีนี้ โปรดติดต่อผู้ดูแลระบบ\n"
    )
    return subject, body


def send_email(*, to: str, subject: str, text_body: str) -> None:
    """ส่งข้อความแบบ plain text; ยก EmailDeliveryError เมื่อ SMTP ส่งไม่สำเร็จ."""
    if not settings.smtp_host:
        raise EmailDeliveryError("SMTP not configured")

    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text_body)

    try:
        with smtplib.SMTP(
            settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds
        ) as smtp:
            if settings.smtp_use_starttls:
                smtp.starttls(context=ssl.create_default_context())
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password or "")
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise EmailDeliveryError("Unable to send email") from exc
