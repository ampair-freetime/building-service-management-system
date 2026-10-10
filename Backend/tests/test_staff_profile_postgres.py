"""Opt-in concurrency checks using a temporary PostgreSQL schema, never app rows."""

import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from conftest import seed_staff
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.models.invitation import StaffInvitation
from app.models.staff import Staff
from app.schemas.staff import StaffUpdate
from app.services import invitations
from app.services import staff as staff_service


@pytest.fixture
def postgres_factory():
    url = os.environ.get("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Set TEST_POSTGRES_URL to run PostgreSQL concurrency tests")
    schema = f"staff_profile_test_{uuid4().hex}"
    admin_engine = create_async_engine(url, poolclass=NullPool)
    engine = create_async_engine(
        url,
        poolclass=NullPool,
        connect_args={"server_settings": {"search_path": schema}},
    )

    async def create():
        async with admin_engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def cleanup():
        await engine.dispose()
        async with admin_engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await admin_engine.dispose()

    try:
        asyncio.run(create())
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        asyncio.run(cleanup())


async def pending_invitation(factory, staff_id, token):
    async with factory() as session:
        invitation = StaffInvitation(
            staff_id=staff_id,
            token_hash=invitations._hash_token(token),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            delivery_status="pending",
        )
        session.add(invitation)
        await session.commit()
        return invitation.id


def test_simultaneous_duplicate_email_rolls_back_profile_and_invitation(
    postgres_factory, monkeypatch
):
    factory = postgres_factory
    actor = seed_staff(factory, email="admin@example.com", password="password", role="admin")
    accounts = [
        seed_staff(factory, email=f"staff{i}@example.com", password="password", role="clerk")
        for i in range(2)
    ]
    original_commit = AsyncSession.commit

    async def run():
        for account in accounts:
            await pending_invitation(factory, account.id, str(account.id))
        barrier = asyncio.Barrier(2)

        async def synchronized_commit(session):
            if session.info.get("profile_race"):
                await barrier.wait()
            await original_commit(session)

        monkeypatch.setattr(AsyncSession, "commit", synchronized_commit)

        async def edit(account):
            async with factory() as session:
                session.info["profile_race"] = True
                return await staff_service.update_staff_profile(
                    session,
                    staff_id=account.id,
                    actor=actor,
                    payload=StaffUpdate(email="shared@example.com", full_name="Changed"),
                )

        results = await asyncio.gather(*(edit(a) for a in accounts), return_exceptions=True)
        assert sum(isinstance(r, Staff) for r in results) == 1
        assert sum(isinstance(r, staff_service.DuplicateStaffError) for r in results) == 1
        async with factory() as session:
            for original in accounts:
                account = await session.get(Staff, original.id)
                invitation = await session.scalar(
                    select(StaffInvitation).where(StaffInvitation.staff_id == original.id)
                )
                if account.email == "shared@example.com":
                    assert account.full_name == "Changed"
                    assert invitation.invalidated_at is not None
                else:
                    assert account.email == original.email
                    assert account.full_name == original.full_name
                    assert invitation.invalidated_at is None
                assert account.password_hash == original.password_hash
                assert account.role == original.role

    asyncio.run(asyncio.wait_for(run(), timeout=20))


@pytest.mark.parametrize("operation", ["activate", "resend"])
def test_email_update_serializes_with_invitation_actions(postgres_factory, monkeypatch, operation):
    factory = postgres_factory
    actor = seed_staff(factory, email="admin@example.com", password="password", role="admin")
    account = seed_staff(factory, email="old@example.com", password="placeholder", role="clerk")
    real_lock = staff_service.get_staff_for_update
    sent = []

    async def fake_send(**kwargs):
        sent.append(kwargs)

    monkeypatch.setattr(invitations, "send_invitation_email", fake_send)

    async def run():
        await pending_invitation(factory, account.id, "old-token")
        locked, attempted, release = asyncio.Event(), asyncio.Event(), asyncio.Event()

        async def held_lock(session, staff_id):
            staff = await real_lock(session, staff_id)
            locked.set()
            await release.wait()
            return staff

        async def observed_lock(session, staff_id):
            attempted.set()
            return await real_lock(session, staff_id)

        monkeypatch.setattr(staff_service, "get_staff_for_update", held_lock)
        monkeypatch.setattr(invitations, "get_staff_for_update", observed_lock)

        async def edit():
            async with factory() as session:
                return await staff_service.update_staff_profile(
                    session,
                    staff_id=account.id,
                    actor=actor,
                    payload=StaffUpdate(email="new@example.com"),
                )

        async def invitation_action():
            async with factory() as session:
                if operation == "activate":
                    with pytest.raises(invitations.InvalidActivationTokenError):
                        await invitations.activate_staff_account(
                            session, token="old-token", password="new-password"
                        )
                else:
                    result = await invitations.resend_staff_invitation(session, account.id)
                    assert result.invitation_sent

        update_task = asyncio.create_task(edit())
        await locked.wait()
        invitation_task = asyncio.create_task(invitation_action())
        try:
            await attempted.wait()
            await asyncio.sleep(0.05)
            assert not invitation_task.done(), "Invitation must wait for the profile transaction"
        finally:
            release.set()
        await asyncio.gather(update_task, invitation_task)
        async with factory() as session:
            stored = await session.get(Staff, account.id)
            assert stored.email == "new@example.com"
            assert stored.password_hash == account.password_hash
            old = await session.scalar(
                select(StaffInvitation).where(
                    StaffInvitation.token_hash == invitations._hash_token("old-token")
                )
            )
            assert old.invalidated_at is not None
            assert old.used_at is None
        if operation == "resend":
            assert len(sent) == 1
            assert sent[0]["recipient"] == "new@example.com"
        else:
            assert sent == []

    asyncio.run(asyncio.wait_for(run(), timeout=20))


def test_email_changed_between_creation_and_delivery_does_not_send_stale_link(
    postgres_factory, monkeypatch
):
    factory = postgres_factory
    actor = seed_staff(factory, email="admin@example.com", password="password", role="admin")
    account = seed_staff(factory, email="old@example.com", password="placeholder", role="clerk")
    sent = []

    async def fake_send(**kwargs):
        sent.append(kwargs)

    monkeypatch.setattr(invitations, "send_invitation_email", fake_send)

    async def run():
        async with factory() as delivery_session:
            stale_account = await delivery_session.get(Staff, account.id)
            invitation, token = await invitations._create_pending_invitation(
                delivery_session, stale_account
            )
            await delivery_session.commit()
            async with factory() as edit_session:
                await staff_service.update_staff_profile(
                    edit_session,
                    staff_id=account.id,
                    actor=actor,
                    payload=StaffUpdate(email="new@example.com"),
                )
            result = await invitations._deliver(delivery_session, stale_account, invitation, token)
            assert not result.invitation_sent
            assert result.staff.email == "new@example.com"
            assert sent == []

    asyncio.run(run())


def test_concurrent_password_reset_confirms_use_link_once(postgres_factory):
    """Two tabs confirming the same reset link: exactly one wins under row locks."""
    from app.core.security import verify_password
    from app.models.password_reset import StaffPasswordReset
    from app.services import password_reset

    factory = postgres_factory
    account = seed_staff(factory, email="tech@example.com", password="Old-Pass1!", role="clerk")
    token = "concurrent-reset-token-value"

    async def run():
        async with factory() as session:
            session.add(
                StaffPasswordReset(
                    staff_id=account.id,
                    token_hash=password_reset._hash_token(token),
                    recipient_email=account.email,
                    expires_at=datetime.now(UTC) + timedelta(minutes=30),
                    created_at=datetime.now(UTC),
                )
            )
            await session.commit()

        async def confirm(new_password):
            async with factory() as session:
                await password_reset.confirm_password_reset(
                    session, token=token, new_password=new_password
                )
                return new_password

        results = await asyncio.gather(
            confirm("First-Pass1!"), confirm("Second-Pass2!"), return_exceptions=True
        )
        winners = [r for r in results if isinstance(r, str)]
        assert len(winners) == 1
        assert sum(isinstance(r, password_reset.InvalidResetTokenError) for r in results) == 1
        async with factory() as session:
            stored = await session.get(Staff, account.id)
            assert verify_password(winners[0], stored.password_hash)
            assert stored.password_changed_at is not None

    asyncio.run(asyncio.wait_for(run(), timeout=20))


def test_two_admins_deleting_each_other_keep_one_active_admin(postgres_factory, monkeypatch):
    """Both requests pass the unlocked check first; the admin-group lock must stop one of them."""
    from app.models.enums import AccountStatus, StaffRole

    factory = postgres_factory
    first = seed_staff(factory, email="admin1@example.com", password="password", role="admin")
    second = seed_staff(factory, email="admin2@example.com", password="password", role="admin")
    real_lock = staff_service.lock_active_admins

    async def run():
        barrier = asyncio.Barrier(2)

        async def lock_after_both_peeked(session):
            await barrier.wait()
            return await real_lock(session)

        monkeypatch.setattr(staff_service, "lock_active_admins", lock_after_both_peeked)

        async def delete(actor, target):
            async with factory() as session:
                await staff_service.delete_staff_account(
                    session, staff_id=target.id, deleted_by=actor
                )
                return target.id

        results = await asyncio.gather(
            delete(first, second), delete(second, first), return_exceptions=True
        )
        assert sum(not isinstance(r, Exception) for r in results) == 1
        assert sum(
            isinstance(r, staff_service.StaffActorNotAuthorizedError) for r in results
        ) == 1
        async with factory() as session:
            active_admins = (
                await session.scalars(
                    select(Staff).where(
                        Staff.role == StaffRole.ADMIN, Staff.status == AccountStatus.ACTIVE
                    )
                )
            ).all()
            assert len(active_admins) == 1

    asyncio.run(asyncio.wait_for(run(), timeout=20))
