"""ตั้งคิวอีเมลยืนยันรับเรื่องของ guest ให้ส่งหลังตอบ response แล้ว."""

import logging

from fastapi import BackgroundTasks, Request

from app.core.config import settings
from app.services.guest_email import SubmissionReceipt, deliver_submission_email
from app.services.rate_limit import SlidingWindowRateLimiter

logger = logging.getLogger(__name__)


def _recipient_limiter(request: Request) -> SlidingWindowRateLimiter:
    """One limiter per application instance, created on first use."""
    limiter = getattr(request.app.state, "guest_email_limiter", None)
    if limiter is None:
        limiter = SlidingWindowRateLimiter(
            limit=settings.guest_email_per_recipient_limit,
            window_seconds=settings.guest_email_per_recipient_window_seconds,
        )
        request.app.state.guest_email_limiter = limiter
    return limiter


def schedule_submission_email(
    request: Request,
    background_tasks: BackgroundTasks,
    *,
    recipient: str,
    receipt: SubmissionReceipt,
) -> None:
    """เรียกหลัง service commit สำเร็จเท่านั้น; ถ้า endpoint raise ภายหลัง FastAPI จะไม่รันงานนี้.

    เกินโควตาของอีเมลผู้รับ = ยังรับคำร้องตามปกติ แต่ไม่ส่งอีเมล เพื่อไม่ให้ใครใช้ฟอร์ม
    ยิงอีเมลใส่คนอื่นรัวๆ และไม่บล็อกคนที่แจ้งเรื่องจริงหลายเรื่องติดกัน
    """
    if not _recipient_limiter(request).allow(recipient.strip().lower()):
        logger.warning(
            "Guest submission email skipped by recipient limit; kind=%s code=%s",
            receipt.kind,
            receipt.code,
        )
        return
    background_tasks.add_task(deliver_submission_email, recipient, receipt)
