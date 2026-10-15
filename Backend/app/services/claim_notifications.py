import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import BackgroundTasks

from app.core.config import settings
from app.services.guest_email import CONTACT_DETAILS, tracking_link
from app.services.invitation_email import EmailDeliveryError, send_email

logger = logging.getLogger(__name__)

BANGKOK_TIMEZONE = ZoneInfo("Asia/Bangkok")

NoticeKind = Literal["rejected", "info_requested", "pickup_scheduled", "released"]

_HELP_DESK = (
    "หากมีข้อสงสัยหรือต้องการสอบถามเพิ่มเติม กรุณาติดต่อเจ้าหน้าที่ที่ห้องธุรการ"
    "หรือห้องประชาสัมพันธ์ ชั้น 1 อาคาร CSB"
)


@dataclass(frozen=True)
class ClaimNotice:
    """สิ่งที่ต้องแจ้งผู้ยื่นคำขอหนึ่งคน; ทุกค่าอ่านมาก่อน commit จึงใช้หลัง session ปิดได้."""

    kind: NoticeKind
    recipient: str
    claimant_name: str
    claim_code: str
    item_name: str
    message: str | None = None  # เหตุผลที่ปฏิเสธ / ข้อมูลที่ขอเพิ่ม / หลักฐานที่ต้องนำมา
    pickup_start: datetime | None = None
    pickup_end: datetime | None = None
    pickup_location: str | None = None


def _bangkok(value: datetime) -> datetime:
    # เวลาที่ไม่มี timezone มาจากฟอร์มของเจ้าหน้าที่ ซึ่งกรอกเป็นเวลาไทย
    if value.tzinfo is None:
        return value.replace(tzinfo=BANGKOK_TIMEZONE)
    return value.astimezone(BANGKOK_TIMEZONE)


def build_claim_email(notice: ClaimNotice) -> tuple[str, str]:
    """คืน (subject, body) ของ notice โดยไม่ต่อ network."""
    greeting = f"เรียน {notice.claimant_name}\n\n"

    if notice.kind == "pickup_scheduled":
        assert notice.pickup_start is not None
        start = _bangkok(notice.pickup_start)
        end = _bangkok(notice.pickup_end) if notice.pickup_end else None
        time_label = start.strftime("%H:%M") + (f"–{end.strftime('%H:%M')}" if end else "")
        subject = f"นัดรับคืน {notice.item_name} · {start.strftime('%d/%m/%Y')}"
        body = (
            greeting
            + "เจ้าหน้าที่ได้กำหนดนัดหมายรับคืนทรัพย์สินของท่าน โดยมีรายละเอียดดังนี้\n\n"
            f"ทรัพย์สิน: {notice.item_name}\n"
            f"รหัสคำขอรับคืน: {notice.claim_code}\n"
            f"วันที่นัดรับคืน: {start.strftime('%d/%m/%Y')}\n"
            f"เวลารับคืน: {time_label} น.\n"
            f"สถานที่รับคืน: {notice.pickup_location or settings.default_custody_location}\n"
            "หลักฐานที่ต้องนำมาเพื่อยืนยันการรับคืน: "
            f"{notice.message or 'ไม่ได้ระบุ กรุณาติดต่อธุรการก่อนเข้ารับของ'}\n\n"
            "หากไม่สะดวกมารับคืนตามวันและเวลาที่กำหนด "
            "กรุณาติดต่อเจ้าหน้าที่ธุรการเพื่อประสานงานนัดหมายใหม่\n\n"
            f"{CONTACT_DETAILS}"
        )
        return subject, body

    if notice.kind == "info_requested":
        subject = f"ขอข้อมูลเพิ่มเติม คำขอรับคืน {notice.item_name} · {notice.claim_code}"
        body = (
            greeting
            + f"คำขอรับคืน: {notice.item_name}\n"
            f"รหัสคำขอรับคืน: {notice.claim_code}\n\n"
            "เจ้าหน้าที่ต้องการข้อมูลเพิ่มเติมเพื่อยืนยันความเป็นเจ้าของ:\n"
            f"{notice.message}\n\n"
            f"ส่งข้อมูลเพิ่มเติมได้ที่: {tracking_link(notice.claim_code)}\n"
            "(ใช้รหัสคำขอคู่กับอีเมลที่ใช้ยื่นคำขอ)\n\n"
            f"{CONTACT_DETAILS}"
        )
        return subject, body

    if notice.kind == "released":
        subject = f"ยกเลิกการรับคืน {notice.item_name} · {notice.claim_code}"
        result = "ยกเลิกการอนุมัติ"
    else:
        subject = f"ผลคำขอรับคืน {notice.item_name} · ไม่อนุมัติ"
        result = "ไม่อนุมัติคำขอ"
    body = (
        greeting
        + f"คำขอรับคืน: {notice.item_name}\n"
        f"รหัสคำขอรับคืน: {notice.claim_code}\n"
        f"ผลการตรวจสอบ: {result}\n"
        f"เหตุผล: {notice.message}\n\n"
        f"{_HELP_DESK}\n\n"
        f"{CONTACT_DETAILS}"
    )
    return subject, body


async def send_claim_notice(notice: ClaimNotice) -> bool:
    """ส่งหนึ่งฉบับ คืน True เมื่อส่งสำเร็จ; ไม่ raise เพราะคำสั่งของเจ้าหน้าที่ commit ไปแล้ว."""
    subject, body = build_claim_email(notice)
    try:
        await send_email(recipient=notice.recipient, subject=subject, body=body)
    except EmailDeliveryError:
        # ไม่ log อีเมลผู้รับ ใช้รหัสคำขอแทนเพื่อตามต่อได้
        logger.warning(
            "Claim email not delivered; kind=%s claim=%s", notice.kind, notice.claim_code
        )
        return False
    return True


def schedule_claim_notices(background_tasks: BackgroundTasks, notices: list[ClaimNotice]) -> None:
    """ส่งหลังตอบ response แล้ว สำหรับอีเมลที่เจ้าหน้าที่ไม่ต้องรอดูผล."""
    for notice in notices:
        background_tasks.add_task(send_claim_notice, notice)
