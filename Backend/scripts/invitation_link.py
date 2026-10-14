"""Print a fresh set-password link for a staff account that is not activated yet.

Use it when the invitation email cannot reach the staff member (SMTP not set up
yet, mail rejected, or the link expired). The link is also emailed when SMTP
works. Every earlier link for that account stops working.

    docker compose exec backend python scripts/invitation_link.py --email staff@example.org
"""

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


async def issue_link(session_factory, email: str) -> int:
    from app.core.config import settings
    from app.services.invitations import InvitationNotAvailableError, resend_staff_invitation
    from app.services.staff import get_staff_by_email

    async with session_factory() as session:
        staff = await get_staff_by_email(session, email)
        if staff is None:
            print(f"No staff account uses {email}. Add the staff member in the admin page first.")
            return 1
        try:
            result = await resend_staff_invitation(session, staff.id)
        except (LookupError, InvitationNotAvailableError) as exc:
            print(f"Cannot issue a link: {exc}")
            return 1

    if result.activation_link is None:
        print("The account changed while issuing the link; run the command again.")
        return 1
    if result.invitation_sent:
        print("The link was also emailed to the staff member.")
    else:
        print("The email could not be sent. Give this link to the staff member yourself:")
    print(result.activation_link)
    print(
        f"It works once and expires in {settings.invitation_token_expire_hours} hours. "
        "Earlier links for this account no longer work."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--email", required=True, help="email of the staff account")
    arguments = parser.parse_args()

    import app.models  # noqa: F401
    from app.db.session import AsyncSessionLocal

    return asyncio.run(issue_link(AsyncSessionLocal, arguments.email))


if __name__ == "__main__":
    raise SystemExit(main())
