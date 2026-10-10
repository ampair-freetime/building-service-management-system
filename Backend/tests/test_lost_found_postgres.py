"""Opt-in race checks for clerk lost & found actions on a temporary PostgreSQL schema."""

import asyncio
from datetime import UTC, datetime

from conftest import seed_staff
from sqlalchemy import func, select
from test_staff_profile_postgres import postgres_factory  # noqa: F401 (pytest fixture)

from app.models.enums import ClaimStatus, LostStatus, LostType, ReturnStatus
from app.models.lost_found import LostClaim, LostClaimReturnStatusHistory, LostItem, LostItemHistory
from app.services import lost_found_clerk


def _seed(factory, *, status, claim_status=None):
    async def seed():
        async with factory() as session:
            item = LostItem(
                item_code=f"FOUND-{datetime.now(UTC):%H%M%S%f}",
                report_type=LostType.FOUND,
                item_category="Accessories",
                item_name="Wallet",
                description="Brown wallet",
                event_datetime=datetime.now(UTC),
                location_detail="Building B",
                custody_location="Clerk Office",
                reporter_email="reporter@example.com",
                status=status,
            )
            session.add(item)
            await session.flush()
            claim_id = None
            if claim_status is not None:
                claim = LostClaim(
                    claim_code=f"CLM-TEST-{datetime.now(UTC):%H%M%S%f}",
                    found_item_id=item.id,
                    claimant_name="Owner",
                    claimant_email="owner@example.com",
                    proof_detail="มีสติกเกอร์ด้านหลัง",
                    status=claim_status,
                )
                session.add(claim)
                await session.flush()
                claim_id = claim.id
            await session.commit()
            return item.id, claim_id

    return asyncio.run(seed())


def test_simultaneous_approve_and_reject_keep_one_decision(postgres_factory, monkeypatch):  # noqa: F811
    """Both clerks pass the request at once; the row lock lets exactly one decide."""
    factory = postgres_factory
    clerk = seed_staff(factory, email="clerk@example.com", password="password", role="clerk")
    item_id, _ = _seed(factory, status=LostStatus.PENDING)
    real_lock = lost_found_clerk._lock_item_for_review

    async def run():
        barrier = asyncio.Barrier(2)

        async def lock_together(session, *args):
            await barrier.wait()
            return await real_lock(session, *args)

        monkeypatch.setattr(lost_found_clerk, "_lock_item_for_review", lock_together)

        async def approve():
            async with factory() as session:
                return await lost_found_clerk.approve_found_item(session, item_id, clerk.id)

        async def reject():
            async with factory() as session:
                return await lost_found_clerk.reject_found_item(
                    session, item_id, clerk.id, "ข้อมูลไม่ครบ"
                )

        results = await asyncio.gather(approve(), reject(), return_exceptions=True)
        assert sum(isinstance(r, LostItem) for r in results) == 1
        assert sum(
            isinstance(r, lost_found_clerk.LostFoundStateConflictError) for r in results
        ) == 1
        async with factory() as session:
            history = await session.scalar(
                select(func.count()).select_from(LostItemHistory).where(
                    LostItemHistory.lost_item_id == item_id
                )
            )
            assert history == 1

    asyncio.run(asyncio.wait_for(run(), timeout=20))


def test_return_status_waits_for_item_lock(postgres_factory):  # noqa: F811
    """While another transaction holds the item, marking it returned must wait, then apply once."""
    factory = postgres_factory
    clerk = seed_staff(factory, email="clerk@example.com", password="password", role="clerk")
    item_id, claim_id = _seed(factory, status=LostStatus.CLAIMED, claim_status=ClaimStatus.APPROVED)

    async def run():
        async with factory() as holder:
            await holder.scalar(select(LostItem).where(LostItem.id == item_id).with_for_update())

            async def mark_returned():
                async with factory() as session:
                    return await lost_found_clerk.update_ownership_return_status(
                        session, claim_id, ReturnStatus.RETURNED, clerk.id
                    )

            first = asyncio.create_task(mark_returned())
            second = asyncio.create_task(mark_returned())
            await asyncio.sleep(0.3)
            assert not first.done() and not second.done(), "Both must wait for the item lock"
            await holder.commit()

        results = await asyncio.gather(first, second, return_exceptions=True)
        assert sum(isinstance(r, LostClaim) for r in results) == 1
        assert sum(
            isinstance(r, lost_found_clerk.LostFoundStateConflictError) for r in results
        ) == 1
        async with factory() as session:
            history = await session.scalar(
                select(func.count()).select_from(LostClaimReturnStatusHistory).where(
                    LostClaimReturnStatusHistory.claim_id == claim_id
                )
            )
            closed = await session.scalar(
                select(func.count()).select_from(LostItemHistory).where(
                    LostItemHistory.lost_item_id == item_id,
                    LostItemHistory.new_status == LostStatus.CLOSED,
                )
            )
            assert history == 1
            assert closed == 1

    asyncio.run(asyncio.wait_for(run(), timeout=20))
