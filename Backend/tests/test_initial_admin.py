"""Bootstrap proof using only temporary SQLite databases and mocked CLI failures."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module

import pytest
from conftest import seed_staff
from sqlalchemy import select

from app.core.security import verify_password
from app.models.staff import Staff
from app.services.auth import authenticate_staff
from scripts import create_initial_admin as bootstrap

TEST_PASSWORD = "Bootstrap-Test9!"


@pytest.fixture
def admin_input(monkeypatch):
    for key, value in {
        "INITIAL_ADMIN_EMAIL": "First.Admin@Example.com",
        "INITIAL_ADMIN_FULL_NAME": "  First   Admin  ",
        "INITIAL_ADMIN_PASSWORD": TEST_PASSWORD,
    }.items():
        monkeypatch.delenv(f"{key}_FILE", raising=False)
        monkeypatch.setenv(key, value)


def accounts(factory):
    async def read():
        async with factory() as session:
            return list((await session.scalars(select(Staff))).all())

    return asyncio.run(read())


def test_create_login_and_repeat_without_credentials(test_context, admin_input, monkeypatch):
    _, factory = test_context
    assert asyncio.run(bootstrap.create_initial_admin(factory)) == "Initial admin created"
    original = accounts(factory)[0]
    assert original.email == "first.admin@example.com"
    assert original.full_name == "First Admin"
    assert original.is_activated
    assert original.password_hash != TEST_PASSWORD
    assert verify_password(TEST_PASSWORD, original.password_hash)

    async def login():
        async with factory() as session:
            assert await authenticate_staff(session, original.email, TEST_PASSWORD)

    asyncio.run(login())
    for name in ("EMAIL", "FULL_NAME", "PASSWORD"):
        monkeypatch.delenv(f"INITIAL_ADMIN_{name}")
    assert "already exists" in asyncio.run(bootstrap.create_initial_admin(factory))
    unchanged = accounts(factory)[0]
    assert unchanged.id == original.id
    assert unchanged.password_hash == original.password_hash
    assert unchanged.updated_at == original.updated_at


@pytest.mark.parametrize("status", ["active", "suspended", "deleted"])
def test_any_existing_admin_blocks_creation(test_context, admin_input, status):
    _, factory = test_context
    existing = seed_staff(
        factory, email="existing@example.com", password=TEST_PASSWORD, role="admin", status=status
    )
    assert "already exists" in asyncio.run(bootstrap.create_initial_admin(factory))
    result = accounts(factory)
    assert len(result) == 1
    assert result[0].password_hash == existing.password_hash
    assert result[0].status.value == status


def test_existing_non_admin_is_never_promoted(test_context, admin_input):
    _, factory = test_context
    existing = seed_staff(
        factory, email="FIRST.ADMIN@example.com", password=TEST_PASSWORD, role="technician"
    )
    with pytest.raises(bootstrap.BootstrapError, match="already belongs"):
        asyncio.run(bootstrap.create_initial_admin(factory))
    result = accounts(factory)
    assert len(result) == 1
    assert result[0].role.value == "technician"
    assert result[0].password_hash == existing.password_hash


@pytest.mark.parametrize(
    "name,value",
    [
        ("EMAIL", "invalid"),
        ("FULL_NAME", "  "),
        ("PASSWORD", "weak"),
        ("PASSWORD", ""),
        ("PASSWORD", "a" * 129),
    ],
)
def test_invalid_input_leaves_database_empty(test_context, admin_input, monkeypatch, name, value):
    _, factory = test_context
    monkeypatch.setenv(f"INITIAL_ADMIN_{name}", value)
    with pytest.raises(bootstrap.BootstrapError):
        asyncio.run(bootstrap.create_initial_admin(factory))
    assert accounts(factory) == []


def test_concurrent_bootstrap_creates_one_admin(test_context, admin_input):
    _, factory = test_context
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(asyncio.run, bootstrap.create_initial_admin(factory)) for _ in range(2)
        ]
        results = [future.result() for future in futures]
    assert sorted(results) == sorted(
        ["Initial admin created", "Admin already exists; no changes made"]
    )
    assert len(accounts(factory)) == 1


def test_secret_files_create_admin(test_context, admin_input, monkeypatch, tmp_path):
    _, factory = test_context
    for name, value in [
        ("EMAIL", "file@example.com"),
        ("FULL_NAME", "File Admin"),
        ("PASSWORD", TEST_PASSWORD),
    ]:
        path = tmp_path / name
        path.write_text(value + "\n")
        path.chmod(0o600)
        monkeypatch.delenv(f"INITIAL_ADMIN_{name}")
        monkeypatch.setenv(f"INITIAL_ADMIN_{name}_FILE", str(path))
    asyncio.run(bootstrap.create_initial_admin(factory))
    assert verify_password(TEST_PASSWORD, accounts(factory)[0].password_hash)


@pytest.mark.parametrize("mode", ["public", "symlink", "missing", "oversized", "conflict"])
def test_unsafe_secret_files_rejected(monkeypatch, tmp_path, mode):
    key = "INITIAL_ADMIN_PASSWORD"
    monkeypatch.delenv(key, raising=False)
    path = tmp_path / "secret"
    path.write_text(TEST_PASSWORD)
    path.chmod(0o600)
    if mode == "public":
        path.chmod(0o644)
    elif mode == "symlink":
        link = tmp_path / "link"
        link.symlink_to(path)
        path = link
    elif mode == "missing":
        path.unlink()
    elif mode == "oversized":
        path.write_text("x" * 4097)
    elif mode == "conflict":
        monkeypatch.setenv(key, TEST_PASSWORD)
    monkeypatch.setenv(f"{key}_FILE", str(path))
    with pytest.raises(bootstrap.BootstrapError) as error:
        bootstrap.read_value(key)
    assert TEST_PASSWORD not in str(error.value)


def test_cli_does_not_log_exception_secrets(monkeypatch, capsys):
    async def failure():
        raise RuntimeError(TEST_PASSWORD)

    monkeypatch.setattr(bootstrap, "run_bootstrap", failure)
    monkeypatch.setattr("sys.argv", ["create_initial_admin.py"])
    assert bootstrap.main() == 1
    assert TEST_PASSWORD not in capsys.readouterr().out


@pytest.mark.parametrize("environment", ["production", "staging", "Production"])
def test_old_seed_skips_non_development(monkeypatch, environment):
    from app.core.config import settings

    migration = import_module("migrations.versions.20260807_0002_seed_initial_staff")
    monkeypatch.setattr(settings, "environment", environment)
    monkeypatch.setattr(migration.op, "execute", lambda _: pytest.fail("Seed must not write"))
    migration.upgrade()


def test_old_seed_still_runs_in_development(monkeypatch):
    from app.core.config import settings

    migration = import_module("migrations.versions.20260807_0002_seed_initial_staff")
    monkeypatch.setattr(settings, "environment", "development")
    writes = []
    monkeypatch.setattr(migration.op, "execute", writes.append)
    migration.upgrade()
    assert len(writes) == 1


@pytest.mark.parametrize("name", ["EMAIL", "FULL_NAME", "PASSWORD"])
def test_missing_input_leaves_database_empty(test_context, admin_input, monkeypatch, name):
    _, factory = test_context
    monkeypatch.delenv(f"INITIAL_ADMIN_{name}")
    with pytest.raises(bootstrap.BootstrapError, match="Missing"):
        asyncio.run(bootstrap.create_initial_admin(factory))
    assert accounts(factory) == []


def test_insert_failure_rolls_back(test_context, admin_input):
    from sqlalchemy import event

    _, factory = test_context

    def reject_insert(*_):
        raise RuntimeError("simulated insert failure")

    event.listen(Staff, "before_insert", reject_insert)
    try:
        with pytest.raises(RuntimeError, match="simulated insert failure"):
            asyncio.run(bootstrap.create_initial_admin(factory))
    finally:
        event.remove(Staff, "before_insert", reject_insert)
    assert accounts(factory) == []
    assert asyncio.run(bootstrap.create_initial_admin(factory)) == "Initial admin created"


def test_postgres_lock_precedes_admin_check():
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, MagicMock

    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    session.begin.return_value.__aenter__ = AsyncMock()
    session.begin.return_value.__aexit__ = AsyncMock(return_value=False)
    session.get_bind.return_value = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
    operations = []

    async def execute(statement):
        operations.append(str(statement))

    async def scalar(_):
        operations.append("admin check")
        return "existing admin"

    session.execute = execute
    session.scalar = scalar
    assert "already exists" in asyncio.run(bootstrap.create_initial_admin(lambda: session))
    assert operations == [
        "SET LOCAL lock_timeout = '10s'",
        "LOCK TABLE staff IN SHARE ROW EXCLUSIVE MODE",
        "admin check",
    ]
    session.add.assert_not_called()


def test_owner_mismatch_names_the_uid_and_the_fix(monkeypatch, tmp_path):
    path = tmp_path / "secret"
    path.write_text(TEST_PASSWORD)
    path.chmod(0o600)
    monkeypatch.delenv("INITIAL_ADMIN_PASSWORD", raising=False)
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD_FILE", str(path))
    # Simulates a Docker container running as another uid than the file owner.
    monkeypatch.setattr(bootstrap.os, "geteuid", lambda: path.stat().st_uid + 1)
    with pytest.raises(bootstrap.BootstrapError, match=r"--user") as error:
        bootstrap.read_value("INITIAL_ADMIN_PASSWORD")
    assert TEST_PASSWORD not in str(error.value)


def test_invalid_input_names_the_field(test_context, admin_input, monkeypatch):
    _, factory = test_context
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "nouppercase1!")
    with pytest.raises(bootstrap.BootstrapError, match="Invalid password: .*uppercase") as error:
        asyncio.run(bootstrap.create_initial_admin(factory))
    assert "nouppercase1!" not in str(error.value)


def _clear_inputs(monkeypatch):
    for name in bootstrap.INPUT_NAMES:
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(f"{name}_FILE", raising=False)


def _use_test_database(monkeypatch, factory):
    """Point run_bootstrap at the test database instead of settings.database_url."""
    import sqlalchemy.ext.asyncio as sqlalchemy_asyncio

    class _Engine:
        async def dispose(self):
            return None

    monkeypatch.setattr(sqlalchemy_asyncio, "create_async_engine", lambda *a, **k: _Engine())
    monkeypatch.setattr(sqlalchemy_asyncio, "async_sessionmaker", lambda *a, **k: factory)


def test_terminal_prompts_create_admin(test_context, monkeypatch):
    _, factory = test_context
    _clear_inputs(monkeypatch)
    _use_test_database(monkeypatch, factory)
    monkeypatch.setattr(bootstrap.sys.stdin, "isatty", lambda: True, raising=False)
    answers = iter(["prompt@example.com", "Prompt Admin"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr("getpass.getpass", lambda _: TEST_PASSWORD)

    assert asyncio.run(bootstrap.run_bootstrap()) == "Initial admin created"
    account = accounts(factory)[0]
    assert account.email == "prompt@example.com"
    assert verify_password(TEST_PASSWORD, account.password_hash)


def test_terminal_does_not_prompt_when_admin_exists(test_context, monkeypatch):
    _, factory = test_context
    seed_staff(factory, email="existing@example.com", password=TEST_PASSWORD, role="admin")
    _clear_inputs(monkeypatch)
    _use_test_database(monkeypatch, factory)
    monkeypatch.setattr(bootstrap.sys.stdin, "isatty", lambda: True, raising=False)
    monkeypatch.setattr("builtins.input", lambda _: pytest.fail("must not prompt"))

    assert "already exists" in asyncio.run(bootstrap.run_bootstrap())


def test_terminal_password_mismatch_creates_nothing(test_context, monkeypatch):
    _, factory = test_context
    _clear_inputs(monkeypatch)
    _use_test_database(monkeypatch, factory)
    monkeypatch.setattr(bootstrap.sys.stdin, "isatty", lambda: True, raising=False)
    answers = iter(["prompt@example.com", "Prompt Admin"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    passwords = iter([TEST_PASSWORD, "Different-Pass9!"])
    monkeypatch.setattr("getpass.getpass", lambda _: next(passwords))

    with pytest.raises(bootstrap.BootstrapError, match="do not match"):
        asyncio.run(bootstrap.run_bootstrap())
    assert accounts(factory) == []
