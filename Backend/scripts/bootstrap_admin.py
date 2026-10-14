"""Create the first admin on an empty production database and send a set-password link.

The account gets a random placeholder password; nobody can log in until the
admin opens the one-time link and chooses a password. When SMTP is not
working, the link is printed so the operator can hand it over directly.
"""

import argparse
import asyncio
import secrets
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


async def bootstrap(email: str, full_name: str) -> int:
    from pydantic import ValidationError
    from sqlalchemy import select

    from app.core.config import settings
    from app.core.security import hash_password
    from app.db.session import AsyncSessionLocal
    from app.models.enums import AccountStatus, StaffRole
    from app.models.staff import Staff
    from app.schemas.staff import StaffCreate

    # Same building blocks as the admin "create staff" API, but this script also
    # needs the raw token so it can print the link when email delivery fails.
    from app.services.invitations import (
        _activation_link,
        _create_pending_invitation,
        _deliver,
    )

    try:
        payload = StaffCreate(email=email, full_name=full_name, role=StaffRole.ADMIN)
    except ValidationError as exc:
        print(f"Invalid input: {exc.errors()[0]['msg']}")
        return 2

    async with AsyncSessionLocal() as session:
        admins = list(
            await session.scalars(
                select(Staff).where(
                    Staff.role == StaffRole.ADMIN,
                    Staff.status != AccountStatus.DELETED,
                )
            )
        )
        if any(admin.is_activated for admin in admins):
            print("An activated admin already exists. Create more staff from the admin page.")
            return 1

        # Re-running with the same email re-issues the link (e.g. it expired before use).
        account = next((admin for admin in admins if admin.email == payload.email), None)
        if account is None and admins:
            print(f"A pending admin already exists: {admins[0].email}. Re-run with that email.")
            return 1
        if account is None:
            account = Staff(
                email=str(payload.email),
                full_name=payload.full_name,
                password_hash=hash_password(secrets.token_urlsafe(48)),
                role=StaffRole.ADMIN,
                status=AccountStatus.ACTIVE,
            )
            session.add(account)
            await session.flush()

        invitation, token = await _create_pending_invitation(session, account)
        await session.commit()
        await session.refresh(invitation)
        result = await _deliver(session, account, invitation, token)

    if result.invitation_sent:
        print(f"Admin {account.email} is ready. A set-password link was emailed.")
    else:
        print(f"Admin {account.email} is ready, but the email could not be sent.")
        print("Open this one-time link to set the password (do not share it):")
        print(_activation_link(token, account.email))
    print(f"The link expires in {settings.invitation_token_expire_hours} hours.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True, help="full name shown in the system")
    arguments = parser.parse_args()
    raise SystemExit(asyncio.run(bootstrap(arguments.email, arguments.name)))


if __name__ == "__main__":
    main()
