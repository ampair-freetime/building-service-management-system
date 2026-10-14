"""Explicit, one-time initial admin bootstrap; never run automatically at startup."""

import asyncio
import os
import stat
import sys
from datetime import UTC, datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


class BootstrapError(Exception):
    """Safe operator-facing error: never include input or database exception details."""


def read_value(name: str) -> str:
    """Read an environment value OR an owner-only UTF-8 secret file on Linux."""
    value = os.environ.get(name)
    filename = os.environ.get(f"{name}_FILE")
    if value is not None and filename is not None:
        raise BootstrapError(f"Set only {name} or {name}_FILE")
    if filename is not None:
        descriptor = None
        try:
            descriptor = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            metadata = os.fstat(descriptor)
            # Name the failed rule (metadata only, never the content) so the operator
            # can fix it. A Docker mount usually fails the owner rule: the file belongs to
            # the host user while the container runs as another uid.
            if not stat.S_ISREG(metadata.st_mode):
                raise BootstrapError(f"{name}_FILE must be a regular file")
            if metadata.st_uid != os.geteuid():
                raise BootstrapError(
                    f"{name}_FILE is owned by uid {metadata.st_uid} but this process runs as "
                    f'uid {os.geteuid()}; in Docker add --user "$(id -u):$(id -g)"'
                )
            if metadata.st_mode & 0o077:
                raise BootstrapError(f"{name}_FILE must not be readable by others (chmod 600)")
            if metadata.st_size > 4096:
                raise BootstrapError(f"{name}_FILE is too large")
            with os.fdopen(descriptor, encoding="utf-8") as source:
                descriptor = None
                value = source.read(4097).rstrip("\r\n")
            if len(value) > 4096:
                raise BootstrapError(f"{name}_FILE is too large")
        except (OSError, UnicodeError):
            raise BootstrapError(f"Cannot securely read {name}_FILE") from None
        finally:
            if descriptor is not None:
                os.close(descriptor)
    if not value:
        raise BootstrapError(f"Missing {name} or {name}_FILE")
    return value


async def create_initial_admin(session_factory) -> str:
    """Create only if no admin exists, serialized against concurrent staff writes."""
    from pydantic import ValidationError
    from sqlalchemy import func, select, text

    from app.core.security import hash_password, validate_password_strength
    from app.models.enums import AccountStatus, StaffRole
    from app.models.staff import Staff
    from app.schemas.staff import StaffCreate

    async with session_factory() as session, session.begin():
        dialect = session.get_bind().dialect.name
        if dialect == "postgresql":
            await session.execute(text("SET LOCAL lock_timeout = '10s'"))
            await session.execute(text("LOCK TABLE staff IN SHARE ROW EXCLUSIVE MODE"))
        elif dialect == "sqlite":  # isolated test databases only
            await session.execute(text("BEGIN IMMEDIATE"))
        else:
            raise BootstrapError("Bootstrap supports PostgreSQL only (SQLite for tests)")
        if await session.scalar(select(Staff.id).where(Staff.role == StaffRole.ADMIN).limit(1)):
            return "Admin already exists; no changes made"
        email = read_value("INITIAL_ADMIN_EMAIL")
        full_name = read_value("INITIAL_ADMIN_FULL_NAME")
        raw_password = read_value("INITIAL_ADMIN_PASSWORD")
        try:
            account = StaffCreate(email=email, full_name=full_name, role=StaffRole.ADMIN)
        except ValidationError as exc:
            # Report the field and rule only; pydantic's full text would repeat the input.
            error = exc.errors()[0]
            raise BootstrapError(f"Invalid {error['loc'][0]}: {error['msg']}") from None
        try:
            password = validate_password_strength(raw_password)
        except ValueError as exc:
            # Messages come from the fixed policy rules and never contain the password.
            raise BootstrapError(f"Invalid password: {exc}") from None
        if await session.scalar(
            select(Staff.id).where(func.lower(Staff.email) == account.email).limit(1)
        ):
            raise BootstrapError("Email already belongs to a staff account; no changes made")
        session.add(
            Staff(
                **account.model_dump(),
                password_hash=hash_password(password),
                status=AccountStatus.ACTIVE,
                password_changed_at=datetime.now(UTC),
                activated_email=account.email,
            )
        )
    return "Initial admin created"


INPUT_NAMES = ("INITIAL_ADMIN_EMAIL", "INITIAL_ADMIN_FULL_NAME", "INITIAL_ADMIN_PASSWORD")


def _missing_inputs() -> list[str]:
    return [
        name
        for name in INPUT_NAMES
        if os.environ.get(name) is None and os.environ.get(f"{name}_FILE") is None
    ]


def _prompt_for_inputs(names: list[str]) -> None:
    """Ask on the terminal; the password is typed hidden and never reaches shell history."""
    from getpass import getpass

    print("No admin exists yet. Enter the first admin account (Ctrl+C to cancel).")
    try:
        if "INITIAL_ADMIN_EMAIL" in names:
            os.environ["INITIAL_ADMIN_EMAIL"] = input("Admin email: ").strip()
        if "INITIAL_ADMIN_FULL_NAME" in names:
            os.environ["INITIAL_ADMIN_FULL_NAME"] = input("Full name: ").strip()
        if "INITIAL_ADMIN_PASSWORD" in names:
            password = getpass("Password (8+ chars with upper, lower, digit and symbol): ")
            if getpass("Repeat password: ") != password:
                raise BootstrapError("Passwords do not match; no changes made")
            os.environ["INITIAL_ADMIN_PASSWORD"] = password
    except (EOFError, KeyboardInterrupt):
        raise BootstrapError("Cancelled; no changes made") from None


async def _admin_exists(session_factory) -> bool:
    from sqlalchemy import select

    from app.models.enums import StaffRole
    from app.models.staff import Staff

    async with session_factory() as session:
        return bool(
            await session.scalar(select(Staff.id).where(Staff.role == StaffRole.ADMIN).limit(1))
        )


async def run_bootstrap() -> str:
    # Import settings only inside the CLI error boundary. No migration is run here.
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    import app.models  # noqa: F401
    from app.core.config import settings

    engine = create_async_engine(settings.database_url, hide_parameters=True, echo=False)
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        missing = _missing_inputs()
        if missing and sys.stdin.isatty():
            # Prompt before taking the table lock so a slow typist never blocks staff writes;
            # create_initial_admin re-checks for an admin under the lock.
            if await _admin_exists(session_factory):
                return "Admin already exists; no changes made"
            _prompt_for_inputs(missing)
        return await create_initial_admin(session_factory)
    finally:
        await engine.dispose()


def main() -> int:
    # No password CLI arguments: avoid shell history / process command-line exposure.
    if len(sys.argv) != 1:
        print(
            "No arguments accepted: run it in a terminal to be prompted, "
            "or set INITIAL_ADMIN_* environment variables or *_FILE"
        )
        return 1
    try:
        result = asyncio.run(run_bootstrap())
    except BootstrapError as exc:
        print(f"Bootstrap stopped: {exc}")
        return 1
    except Exception:  # noqa: BLE001 - CLI boundary must never expose secrets
        # Validation/DB exceptions may embed passwords, URLs or SQL parameters.
        print(
            "Bootstrap failed; check configuration, schema and database access. No secrets logged"
        )
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
