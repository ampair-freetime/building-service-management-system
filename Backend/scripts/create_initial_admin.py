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
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.geteuid()
                or metadata.st_mode & 0o077
                or metadata.st_size > 4096
            ):
                raise BootstrapError(f"{name}_FILE must be a small, owner-only regular file")
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
        try:
            account = StaffCreate(
                email=read_value("INITIAL_ADMIN_EMAIL"),
                full_name=read_value("INITIAL_ADMIN_FULL_NAME"),
                role=StaffRole.ADMIN,
            )
            password = validate_password_strength(read_value("INITIAL_ADMIN_PASSWORD"))
        except ValueError:
            raise BootstrapError("Invalid initial admin email, name or password policy") from None
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


async def run_bootstrap() -> str:
    # Import settings only inside the CLI error boundary. No migration is run here.
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    import app.models  # noqa: F401
    from app.core.config import settings

    engine = create_async_engine(settings.database_url, hide_parameters=True, echo=False)
    try:
        return await create_initial_admin(async_sessionmaker(engine, expire_on_commit=False))
    finally:
        await engine.dispose()


def main() -> int:
    # No password CLI arguments: avoid shell history / process command-line exposure.
    if len(sys.argv) != 1:
        print("Use INITIAL_ADMIN_* environment variables or *_FILE; no arguments accepted")
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
