"""Self-service staff password reset: request, deliver, validate, and confirm a link."""

import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.models.enums import AccountStatus
from app.models.invitation import StaffInvitation
from app.models.password_reset import StaffPasswordReset
from app.models.staff import Staff
from app.services.invitation_email import EmailDeliveryError, send_password_reset_email
from app.services.staff import get_staff_by_email, get_staff_for_update

logger = logging.getLogger(__name__)

INVALID_RESET_LINK_MESSAGE = "Invalid or expired reset link. Request a new one."


class InvalidResetTokenError(ValueError):
    """Reset token is unknown, expired, superseded, already used, or for an old address."""


@dataclass(frozen=True)
class PendingPasswordReset:
    """What the background delivery needs; the raw token never touches the database."""

    reset_id: UUID
    token: str


def _now() -> datetime:
    return datetime.now(UTC)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _reset_link(token: str) -> str:
    # The address is deliberately not part of the URL: it would leak through
    # access logs, browser history and the Referer header.
    separator = "&" if "?" in settings.staff_password_reset_url else "?"
    return f"{settings.staff_password_reset_url}{separator}{urlencode({'token': token})}"


def _is_eligible(staff: Staff | None) -> bool:
    # Accounts that never activated (password_changed_at is NULL) must use their
    # invitation instead; deleted or suspended accounts get nothing.
    return (
        staff is not None
        and staff.status == AccountStatus.ACTIVE
        and staff.password_changed_at is not None
    )


async def invalidate_pending_resets(session: AsyncSession, staff_id: UUID) -> None:
    """Make every unused reset link of this account unusable. The caller commits."""
    await session.execute(
        update(StaffPasswordReset)
        .where(
            StaffPasswordReset.staff_id == staff_id,
            StaffPasswordReset.used_at.is_(None),
            StaffPasswordReset.invalidated_at.is_(None),
        )
        .values(invalidated_at=_now())
    )


async def request_password_reset(
    session: AsyncSession, email: str
) -> PendingPasswordReset | None:
    """Create a fresh link for an eligible account, or return None without saying why."""
    candidate = await get_staff_by_email(session, email)
    if not _is_eligible(candidate):
        return None
    # Lock the account like activation and email changes do, then re-check.
    staff = await get_staff_for_update(session, candidate.id)
    if not _is_eligible(staff):
        await session.rollback()
        return None

    now = _now()
    if settings.password_reset_cooldown_seconds:
        recent = await session.scalar(
            select(StaffPasswordReset.id).where(
                StaffPasswordReset.staff_id == staff.id,
                StaffPasswordReset.created_at
                > now - timedelta(seconds=settings.password_reset_cooldown_seconds),
            )
        )
        if recent is not None:
            await session.rollback()
            return None

    await invalidate_pending_resets(session, staff.id)
    token = secrets.token_urlsafe(32)
    reset = StaffPasswordReset(
        staff_id=staff.id,
        token_hash=_hash_token(token),
        recipient_email=staff.email,
        expires_at=now + timedelta(minutes=settings.password_reset_token_expire_minutes),
        delivery_status="pending",
        # Set in Python so cooldown comparisons use one timestamp source.
        created_at=now,
    )
    session.add(reset)
    # Commit before any email work so no row lock is held while talking to SMTP.
    await session.commit()
    return PendingPasswordReset(reset_id=reset.id, token=token)


async def deliver_password_reset(
    session_factory: async_sessionmaker[AsyncSession], pending: PendingPasswordReset
) -> None:
    """Background task: email the link and record the outcome in a new session.

    The request's session is already closed when this runs, so it opens its own.
    """
    async with session_factory() as session:
        recipient = await session.scalar(
            select(StaffPasswordReset.recipient_email)
            .join(Staff)
            .where(
                StaffPasswordReset.id == pending.reset_id,
                StaffPasswordReset.used_at.is_(None),
                StaffPasswordReset.invalidated_at.is_(None),
                StaffPasswordReset.expires_at > _now(),
                Staff.status == AccountStatus.ACTIVE,
                Staff.email == StaffPasswordReset.recipient_email,
            )
        )
        if recipient is None:
            await _record_delivery(session, pending.reset_id, "failed")
            return
        try:
            await send_password_reset_email(
                recipient=recipient,
                reset_link=_reset_link(pending.token),
                expires_in_minutes=settings.password_reset_token_expire_minutes,
            )
        except EmailDeliveryError:
            # Never log the token, link or raw SMTP error text.
            logger.warning("Password reset delivery failed; reset_id=%s", pending.reset_id)
            await _record_delivery(session, pending.reset_id, "failed")
            return
        await _record_delivery(session, pending.reset_id, "sent", sent_at=_now())
        logger.info("Password reset delivered; reset_id=%s", pending.reset_id)


async def _record_delivery(
    session: AsyncSession, reset_id: UUID, status: str, *, sent_at: datetime | None = None
) -> None:
    values: dict[str, object] = {"delivery_status": status}
    if sent_at is not None:
        values["sent_at"] = sent_at
    await session.execute(
        update(StaffPasswordReset).where(StaffPasswordReset.id == reset_id).values(**values)
    )
    await session.commit()


def _usable_link_conditions(token: str):
    return (
        StaffPasswordReset.token_hash == _hash_token(token),
        StaffPasswordReset.used_at.is_(None),
        StaffPasswordReset.invalidated_at.is_(None),
        StaffPasswordReset.expires_at > _now(),
    )


async def validate_reset_token(session: AsyncSession, token: str) -> None:
    """Raise when the link can no longer be used; nothing is changed."""
    reset_id = await session.scalar(
        select(StaffPasswordReset.id)
        .join(Staff)
        .where(
            *_usable_link_conditions(token),
            Staff.status == AccountStatus.ACTIVE,
            Staff.email == StaffPasswordReset.recipient_email,
        )
    )
    if reset_id is None:
        raise InvalidResetTokenError(INVALID_RESET_LINK_MESSAGE)


async def confirm_password_reset(
    session: AsyncSession, *, token: str, new_password: str
) -> None:
    """Consume the link and replace the password in one transaction."""
    target_id = await session.scalar(
        select(StaffPasswordReset.staff_id).where(
            StaffPasswordReset.token_hash == _hash_token(token)
        )
    )
    # Lock Staff first (same order as activation and email updates), then consume
    # the token with a conditional UPDATE so two concurrent confirms cannot both win.
    staff = await get_staff_for_update(session, target_id) if target_id is not None else None
    if staff is None or staff.status != AccountStatus.ACTIVE:
        await session.rollback()
        raise InvalidResetTokenError(INVALID_RESET_LINK_MESSAGE)

    now = _now()
    consumed = await session.scalar(
        update(StaffPasswordReset)
        .where(
            *_usable_link_conditions(token),
            StaffPasswordReset.recipient_email == staff.email,
        )
        .values(used_at=now)
        .returning(StaffPasswordReset.id)
    )
    if consumed is None:
        await session.rollback()
        raise InvalidResetTokenError(INVALID_RESET_LINK_MESSAGE)

    staff.password_hash = hash_password(new_password)
    # Every access token issued before this instant stops working.
    staff.password_changed_at = now
    await invalidate_pending_resets(session, staff.id)
    await session.execute(
        update(StaffInvitation)
        .where(
            StaffInvitation.staff_id == staff.id,
            StaffInvitation.used_at.is_(None),
            StaffInvitation.invalidated_at.is_(None),
        )
        .values(invalidated_at=now)
    )
    await session.commit()
    logger.info("Password reset completed; staff_id=%s", staff.id)
