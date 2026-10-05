"""Unit tests for the pieces behind password reset: limiter, rules, migration, email."""

import asyncio
import importlib

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.core.config import Settings
from app.core.security import validate_password_strength
from app.services import invitation_email
from app.services.rate_limit import SlidingWindowRateLimiter


def test_sliding_window_limits_per_key_and_recovers() -> None:
    now = [0.0]
    limiter = SlidingWindowRateLimiter(limit=2, window_seconds=10, clock=lambda: now[0])
    assert limiter.allow("a") and limiter.allow("a")
    assert not limiter.allow("a")
    assert limiter.allow("b")
    now[0] = 10.5
    assert limiter.allow("a")


def test_sliding_window_prunes_idle_keys() -> None:
    now = [0.0]
    limiter = SlidingWindowRateLimiter(
        limit=1, window_seconds=1, max_keys=2, clock=lambda: now[0]
    )
    limiter.allow("a")
    limiter.allow("b")
    now[0] = 5
    assert limiter.allow("c")
    assert set(limiter._hits) == {"c"}


@pytest.mark.parametrize(
    ("password", "valid"),
    [
        ("Good-Pass1", True),
        ("Aa1!aaaa", True),
        ("Aa1!aaa", False),
        ("Aa1!" + "a" * 125, False),
        ("lower-case1", False),
        ("UPPER-CASE1", False),
        ("No-Digits!", False),
        ("NoSpecial12", False),
    ],
)
def test_password_rule_matches_frontend_checklist(password: str, valid: bool) -> None:
    if valid:
        assert validate_password_strength(password) == password
    else:
        with pytest.raises(ValueError):
            validate_password_strength(password)


def test_reset_email_contains_link_and_expiry(monkeypatch) -> None:
    monkeypatch.setattr(
        invitation_email, "settings", Settings(_env_file=None, smtp_host="relay.example.org")
    )
    sent = []

    class Connection:
        def __init__(self, **options):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def starttls(self, *, context):
            pass

        def send_message(self, message):
            sent.append(message)

    monkeypatch.setattr(invitation_email.smtplib, "SMTP", Connection)
    asyncio.run(
        invitation_email.send_password_reset_email(
            recipient="staff@example.org",
            reset_link="https://care.example.org/staff/reset-password?token=abc",
            expires_in_minutes=30,
        )
    )
    [message] = sent
    body = message.get_content()
    assert message["To"] == "staff@example.org"
    assert "https://care.example.org/staff/reset-password?token=abc" in body
    assert "30 minutes" in body


def test_password_reset_migration_backfills_and_rolls_back(tmp_path) -> None:
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'reset.db'}")
    metadata = sa.MetaData()
    staff = sa.Table(
        "staff",
        metadata,
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.String(30)),
    )
    invitations = sa.Table(
        "staff_invitations",
        metadata,
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("staff_id", sa.String(36)),
        sa.Column("used_at", sa.String(30), nullable=True),
    )
    metadata.create_all(engine)
    migration = importlib.import_module(
        "migrations.versions.20261006_0016_add_staff_password_resets"
    )

    with engine.begin() as connection:
        connection.execute(
            staff.insert(),
            [
                {"id": "seeded", "created_at": "2026-08-07 00:00:00"},
                {"id": "activated", "created_at": "2026-09-01 00:00:00"},
                {"id": "pending", "created_at": "2026-09-02 00:00:00"},
            ],
        )
        connection.execute(
            invitations.insert(),
            [
                {"id": "i1", "staff_id": "activated", "used_at": "2026-09-03 08:00:00"},
                {"id": "i2", "staff_id": "pending", "used_at": None},
            ],
        )
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        changed = dict(
            connection.execute(sa.text("SELECT id, password_changed_at FROM staff")).all()
        )
        assert str(changed["seeded"]).startswith("2026-08-07")
        assert str(changed["activated"]).startswith("2026-09-03 08:00")
        assert changed["pending"] is None
        assert "staff_password_resets" in sa.inspect(connection).get_table_names()

        migration.downgrade()
        inspector = sa.inspect(connection)
        assert "staff_password_resets" not in inspector.get_table_names()
        assert "password_changed_at" not in {c["name"] for c in inspector.get_columns("staff")}
    engine.dispose()
