"""Creation, delivery, validation, and one-time use of staff invitations."""

import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.enums import AccountStatus
from app.models.invitation import StaffInvitation
from app.models.staff import Staff
from app.schemas.staff import StaffCreate
from app.services.invitation_email import EmailDeliveryError, send_invitation_email
from app.services.password_reset import invalidate_pending_resets
from app.services.staff import DuplicateStaffError, get_staff_for_update

logger = logging.getLogger(__name__)


class InvalidActivationTokenError(ValueError):
    """Activation token is unknown, expired, superseded, or has already been used."""


class InvitationNotAvailableError(ValueError):
    """The account is not eligible to receive another first-time invitation."""


@dataclass(frozen=True)
class InvitationResult:
    staff: Staff
    invitation_sent: bool
    delivery_status: str


def _now() -> datetime:
    return datetime.now(UTC)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _activation_link(token: str, email: str) -> str:
    separator = "&" if "?" in settings.staff_activation_url else "?"
    return f"{settings.staff_activation_url}{separator}{urlencode({'token': token, 'email': email})}"


async def _create_pending_invitation(
    session: AsyncSession, staff: Staff
) -> tuple[StaffInvitation, str]:
    now = _now()
    # A resend makes every previous, unconsumed link unusable before the new one exists.
    await session.execute(
        update(StaffInvitation)
        .where(
            StaffInvitation.staff_id == staff.id,
            StaffInvitation.used_at.is_(None),
            StaffInvitation.invalidated_at.is_(None),
        )
        .values(invalidated_at=now)
    )
    token = secrets.token_urlsafe(32)
    invitation = StaffInvitation(
        staff_id=staff.id,
        token_hash=_hash_token(token),
        expires_at=now + timedelta(hours=settings.invitation_token_expire_hours),
        delivery_status="pending",
    )
    session.add(invitation)
    return invitation, token


async def _deliver(
    session: AsyncSession, staff: Staff, invitation: StaffInvitation, token: str
) -> InvitationResult:
    # Re-read under the same account lock as email update/resend/activation.
    # An email changed between creation and delivery must never receive an old link.
    current_staff = await get_staff_for_update(session, staff.id)
    current_invitation = await session.scalar(
        select(StaffInvitation)
        .where(
            StaffInvitation.id == invitation.id,
            StaffInvitation.used_at.is_(None),
            StaffInvitation.invalidated_at.is_(None),
            StaffInvitation.expires_at > _now(),
        )
        .execution_options(populate_existing=True)
    )
    if (
        current_staff is None
        or current_staff.status != AccountStatus.ACTIVE
        or current_invitation is None
    ):
        invitation.delivery_status = "failed"
        await session.commit()
        return InvitationResult(staff, False, "failed")
    try:
        await send_invitation_email(
            recipient=staff.email,
            # Email is the current staff identifier and is included in the invitation.
            staff_identifier=staff.email,
            activation_link=_activation_link(token, staff.email),
        )
    except EmailDeliveryError:
        # Keep a safe delivery result in the audit record. Do not persist raw SMTP
        # errors because they can contain credentials or provider details.
        invitation.delivery_status = "failed"
        await session.commit()
        logger.warning("Staff invitation delivery failed; staff_id=%s", staff.id)
        return InvitationResult(staff, False, "failed")

    invitation.delivery_status = "sent"
    invitation.sent_at = _now()
    await session.commit()
    logger.info("Staff invitation delivered; staff_id=%s", staff.id)
    return InvitationResult(staff, True, "sent")


async def create_staff_and_invite(
    session: AsyncSession, payload: StaffCreate
) -> InvitationResult:
    """Persist the account before attempting mail, so a failed delivery can be retried."""
    # This random value is never returned or emailed. Login is impossible until the
    # staff member completes activation and chooses a real password.
    account = Staff(
        email=str(payload.email),
        full_name=payload.full_name,
        password_hash=hash_password(secrets.token_urlsafe(48)),
        role=payload.role,
        status=AccountStatus.ACTIVE,
    )
    session.add(account)
    try:
        await session.flush()
        invitation, token = await _create_pending_invitation(session, account)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateStaffError("Email already exists") from exc
    await session.refresh(account)
    await session.refresh(invitation)
    return await _deliver(session, account, invitation, token)


async def resend_staff_invitation(session: AsyncSession, staff_id: UUID) -> InvitationResult:
    staff = await get_staff_for_update(session, staff_id)
    if staff is None or staff.status == AccountStatus.DELETED:
        raise LookupError("Staff account not found")
    if staff.status != AccountStatus.ACTIVE:
        raise InvitationNotAvailableError("Account is not active")

    if staff.is_activated:
        raise InvitationNotAvailableError("Account has already been activated")

    invitation, token = await _create_pending_invitation(session, staff)
    await session.commit()
    await session.refresh(invitation)
    return await _deliver(session, staff, invitation, token)


async def validate_activation_token(session: AsyncSession, token: str) -> None:
    invitation = await session.scalar(
        select(StaffInvitation.id).join(Staff).where(
            StaffInvitation.token_hash == _hash_token(token),
            StaffInvitation.used_at.is_(None),
            StaffInvitation.invalidated_at.is_(None),
            StaffInvitation.expires_at > _now(),
            Staff.status == AccountStatus.ACTIVE,
        )
    )
    if invitation is None:
        raise InvalidActivationTokenError(
            "Invalid or expired activation link. Request a new invitation."
        )


async def activate_staff_account(session: AsyncSession, *, token: str, password: str) -> None:
    """Consume a token atomically, then replace the placeholder password hash."""
    # Lock Staff before updating the invitation, matching email update/resend.
    target_id = await session.scalar(
        select(StaffInvitation.staff_id).where(
            StaffInvitation.token_hash == _hash_token(token)
        )
    )
    staff = await get_staff_for_update(session, target_id) if target_id is not None else None
    if staff is None or staff.status != AccountStatus.ACTIVE:
        await session.rollback()
        raise InvalidActivationTokenError(
            "Invalid or expired activation link. Request a new invitation."
        )
    staff_id = await session.scalar(
        update(StaffInvitation)
        .where(
            StaffInvitation.token_hash == _hash_token(token),
            StaffInvitation.used_at.is_(None),
            StaffInvitation.invalidated_at.is_(None),
            StaffInvitation.expires_at > _now(),
        )
        .values(used_at=_now())
        .returning(StaffInvitation.staff_id)
    )
    if staff_id is None:
        await session.rollback()
        raise InvalidActivationTokenError(
            "Invalid or expired activation link. Request a new invitation."
        )
    staff.password_hash = hash_password(password)
    staff.password_changed_at = _now()
    staff.activated_email = staff.email
    await invalidate_pending_resets(session, staff.id)
    await session.commit()
