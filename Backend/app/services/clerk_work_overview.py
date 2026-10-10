"""Queries backing the admin clerk-approval overview."""

from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import LostStatus, LostType
from app.models.lost_found import LostClaim, LostItem
from app.schemas.clerk_work_overview import (
    AnnouncementStatistics,
    ClerkAnnouncementListItem,
    ClerkAnnouncementListResponse,
    ClerkApprovalMetric,
    ClerkWorkOverviewResponse,
    ClerkClaimOverviewItem,
)


def _date_filters(date_from: date | None, date_to: date | None) -> list[object]:
    """Apply inclusive UTC calendar-date bounds to submission timestamps."""
    filters: list[object] = []
    if date_from is not None:
        filters.append(LostItem.created_at >= datetime.combine(date_from, time.min, UTC))
    if date_to is not None:
        filters.append(
            LostItem.created_at < datetime.combine(date_to + timedelta(days=1), time.min, UTC)
        )
    return filters


def _statistics_statement(
    *, announcement_type: LostType | None, date_from: date | None, date_to: date | None
):
    filters = _date_filters(date_from, date_to)
    if announcement_type is not None:
        filters.append(LostItem.report_type == announcement_type)

    return select(
        func.count(LostItem.id).label("total"),
        func.coalesce(
            func.sum(case((LostItem.status == LostStatus.APPROVED, 1), else_=0)), 0
        ).label("approved"),
        func.coalesce(
            func.sum(case((LostItem.status == LostStatus.REJECTED, 1), else_=0)), 0
        ).label("rejected"),
    ).where(*filters)


def _age_hours(created_at: datetime, now: datetime) -> float:
    created_at_utc = created_at.replace(tzinfo=UTC) if created_at.tzinfo is None else created_at
    return round(max(0.0, (now - created_at_utc).total_seconds() / 3600), 2)


async def get_clerk_work_overview(
    session: AsyncSession,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    announcement_type: LostType | None = None,
) -> ClerkWorkOverviewResponse:
    """Return approval and pending-review metrics across every clerk."""
    types = (LostType.LOST, LostType.FOUND)
    rows = {
        item_type: (
            await session.execute(
                _statistics_statement(
                    announcement_type=item_type, date_from=date_from, date_to=date_to
                )
            )
        ).one()
        for item_type in types
    }
    overall = (
        await session.execute(
            _statistics_statement(
                announcement_type=announcement_type, date_from=date_from, date_to=date_to
            )
        )
    ).one()
    pending_filters = _date_filters(date_from, date_to)
    if announcement_type is not None:
        pending_filters.append(LostItem.report_type == announcement_type)
    pending_rows = await session.execute(
        select(LostItem.report_type, LostItem.created_at).where(
            *pending_filters, LostItem.status == LostStatus.PENDING
        )
    )
    now = datetime.now(UTC)
    pending_ages: dict[LostType, list[float]] = {item_type: [] for item_type in types}
    for item_type, created_at in pending_rows:
        pending_ages[item_type].append(_age_hours(created_at, now))

    def statistics(row: object, ages: list[float]) -> AnnouncementStatistics:
        return AnnouncementStatistics(
            total=row.total,
            approved=row.approved,
            rejected=row.rejected,
            pending_review=len(ages),
            oldest_pending_review_age_hours=max(ages) if ages else None,
            average_pending_review_age_hours=round(sum(ages) / len(ages), 2) if ages else None,
        )

    selected_ages = (
        pending_ages[announcement_type]
        if announcement_type is not None
        else [age for ages in pending_ages.values() for age in ages]
    )
    claim_filters = []
    if date_from is not None:
        claim_filters.append(LostClaim.created_at >= datetime.combine(date_from, time.min, UTC))
    if date_to is not None:
        claim_filters.append(LostClaim.created_at < datetime.combine(date_to + timedelta(days=1), time.min, UTC))
    if announcement_type is not None:
        claim_filters.append(LostItem.report_type == announcement_type)
    claim_rows = await session.execute(
        select(LostClaim, LostItem.item_name)
        .join(LostItem, LostClaim.found_item_id == LostItem.id)
        .where(*claim_filters)
        .order_by(LostClaim.created_at.desc(), LostClaim.claim_code.asc())
    )
    claims = [
        ClerkClaimOverviewItem(
            id=claim.id, claim_code=claim.claim_code, item_name=item_name,
            claimant_name=claim.claimant_name, claimant_email=claim.claimant_email,
            status=claim.status, return_status=claim.return_status,
            proof_detail=claim.proof_detail, staff_message=claim.staff_message,
            submission_date=claim.created_at, updated_at=claim.updated_at,
        )
        for claim, item_name in claim_rows
    ]
    return ClerkWorkOverviewResponse(
        claims=claims,
        summary=statistics(overall, selected_ages),
        by_announcement_type={
            item_type: statistics(rows[item_type], pending_ages[item_type]) for item_type in types
        },
        date_from=date_from,
        date_to=date_to,
        announcement_type=announcement_type,
    )


async def list_clerk_work_announcements(
    session: AsyncSession,
    *,
    metric: ClerkApprovalMetric,
    announcement_type: LostType | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> ClerkAnnouncementListResponse:
    """Return the announcements represented by a selected dashboard metric."""
    filters = _date_filters(date_from, date_to)
    if announcement_type is not None:
        filters.append(LostItem.report_type == announcement_type)
    if metric == "approved":
        filters.append(LostItem.status == LostStatus.APPROVED)
    elif metric == "rejected":
        filters.append(LostItem.status == LostStatus.REJECTED)
    elif metric == "pending_review":
        filters.append(LostItem.status == LostStatus.PENDING)

    result = await session.scalars(
        select(LostItem).where(*filters).order_by(LostItem.created_at.desc(), LostItem.item_code.asc())
    )
    now = datetime.now(UTC)
    announcements = [
        ClerkAnnouncementListItem(
            id=item.id,
            item_code=item.item_code,
            announcement_type=item.report_type,
            submission_date=item.created_at,
            status=item.status,
            pending_review_age_hours=(
                _age_hours(item.created_at, now) if item.status == LostStatus.PENDING else None
            ),
        )
        for item in result.all()
    ]
    return ClerkAnnouncementListResponse(
        metric=metric,
        announcement_type=announcement_type,
        date_from=date_from,
        date_to=date_to,
        total=len(announcements),
        announcements=announcements,
    )
