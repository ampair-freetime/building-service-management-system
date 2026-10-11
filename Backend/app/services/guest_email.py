"""อีเมลยืนยันรับเรื่องที่ส่งให้ guest พร้อมรหัสสำหรับติดตามสถานะ.

guest ไม่ต้องยืนยันอีเมลก่อนส่งคำร้อง ใครก็กรอกอีเมลของคนอื่นได้ เนื้อหาอีเมลจึงมีได้แค่
ข้อมูลที่ระบบสร้างเอง (รหัส ประเภท ชื่อสถานที่จากตาราง locations เวลา ลิงก์) ห้ามใส่ข้อความ
ที่ guest พิมพ์ เช่น title หรือ description เพราะจะกลายเป็นช่องทางส่งข้อความใดๆ ในนามโดเมนนี้
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.services.invitation_email import EmailDeliveryError, send_email

logger = logging.getLogger(__name__)

BANGKOK_TIMEZONE = ZoneInfo("Asia/Bangkok")

SubmissionKind = Literal["cleaning", "repair", "lost", "found", "claim"]

# (ชื่อประเภทในอีเมล, ขั้นตอนถัดไปที่ guest ควรรู้)
_KIND_TEXT: dict[str, tuple[str, str]] = {
    "cleaning": ("แจ้งทำความสะอาด", "แม่บ้านจะรับงานและอัปเดตสถานะในระบบ"),
    "repair": ("แจ้งซ่อม", "ช่างจะรับงานและอัปเดตสถานะในระบบ"),
    "lost": ("ประกาศของหาย", "ประกาศจะแสดงต่อสาธารณะหลังเจ้าหน้าที่ตรวจสอบ"),
    "found": ("แจ้งพบของ", "กรุณานำของไปฝากที่จุดรับฝากตามที่หน้าเว็บแจ้ง"),
    "claim": ("คำขอรับของคืน", "เจ้าหน้าที่จะตรวจสอบหลักฐานและแจ้งผลทางอีเมล"),
}

CONTACT_FOOTER = (
    "ช่องทางติดต่อ\n"
    "โทรศัพท์: 053-943433 หรือ 063-0807969\n"
    "อีเมล: Compsci@cmu.ac.th\n"
    "เวลาทำการ: วันจันทร์–ศุกร์ เวลา 08:30–16:30 น. (ยกเว้นวันหยุดนักขัตฤกษ์)\n\n"
    "อีเมลนี้ส่งอัตโนมัติ กรุณาอย่าตอบกลับ หากท่านไม่ได้ส่งคำร้องนี้ สามารถละเว้นอีเมลนี้ได้"
)


@dataclass(frozen=True)
class SubmissionReceipt:
    """ข้อมูลที่ระบบสร้างเองทั้งหมด จึงใส่ในอีเมลได้อย่างปลอดภัย."""

    kind: SubmissionKind
    code: str
    created_at: datetime
    location_label: str | None = None
    related_code: str | None = None  # claim อ้างถึงรหัสประกาศพบของ


def tracking_link(code: str) -> str:
    """ใส่เฉพาะรหัส ไม่ใส่อีเมล เพราะ URL ถูกเก็บใน history ของ browser และ log ของ proxy."""
    return f"{settings.public_base_url.rstrip('/')}/user?{urlencode({'track': code})}"


def _bangkok_time(value: datetime) -> str:
    # ค่าจาก DB มี timezone; ค่าที่ไม่มี timezone ถือว่าเป็น UTC แบบเดียวกับที่ DB เก็บ
    aware = value if value.tzinfo else value.replace(tzinfo=UTC)
    return aware.astimezone(BANGKOK_TIMEZONE).strftime("%d/%m/%Y %H:%M")


def build_submission_email(receipt: SubmissionReceipt) -> tuple[str, str]:
    """คืน (subject, body) โดยไม่ต่อ network เพื่อให้ทดสอบเนื้อหาได้ตรงๆ."""
    kind_label, next_step = _KIND_TEXT[receipt.kind]
    lines = [
        "เรียน ผู้แจ้ง",
        "",
        "ระบบได้รับเรื่องของท่านแล้ว",
        f"ประเภท: {kind_label}",
        f"รหัสสำหรับติดตาม: {receipt.code}",
    ]
    if receipt.related_code:
        lines.append(f"รหัสประกาศที่ขอรับคืน: {receipt.related_code}")
    if receipt.location_label:
        lines.append(f"สถานที่: {receipt.location_label}")
    lines += [
        f"เวลาที่รับเรื่อง: {_bangkok_time(receipt.created_at)} น.",
        "",
        next_step,
        "",
        f"ติดตามสถานะได้ที่: {tracking_link(receipt.code)}",
        "(ใช้รหัสนี้คู่กับอีเมลที่ใช้ส่งเรื่อง)",
        "",
        CONTACT_FOOTER,
    ]
    subject = f"ได้รับเรื่อง{kind_label}แล้ว · {receipt.code}"
    return subject, "\n".join(lines)


async def deliver_submission_email(recipient: str, receipt: SubmissionReceipt) -> None:
    """Background task หลังตอบ response แล้ว จึงต้องไม่ raise ออกไป เพราะไม่มีใครรับ error ต่อ."""
    subject, body = build_submission_email(receipt)
    try:
        await send_email(recipient=recipient, subject=subject, body=body)
    except EmailDeliveryError as exc:
        # ไม่ log อีเมลผู้รับหรือข้อความดิบจาก SMTP (มักมีที่อยู่ผู้รับอยู่ในนั้น) แค่ชนิด error
        # กับรหัส SMTP ก็พอแยกได้ว่าเป็น timeout, login ไม่ผ่าน หรือ Gmail ปฏิเสธ
        cause = exc.__cause__
        logger.warning(
            "Guest submission email not delivered; kind=%s code=%s reason=%s smtp_code=%s",
            receipt.kind,
            receipt.code,
            type(cause).__name__ if cause else "not configured",
            getattr(cause, "smtp_code", None),
        )
        return
    logger.info("Guest submission email delivered; kind=%s code=%s", receipt.kind, receipt.code)
