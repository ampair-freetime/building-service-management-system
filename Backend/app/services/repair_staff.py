"""Business logic สำหรับ Repair Staff."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from uuid import UUID
from app.models.enums import RequestType
from app.models.service_request import ServiceRequest


async def list_repair_requests(
    session: AsyncSession,
) -> list[ServiceRequest]:
    """ดึงรายการ repair requests โดยเรียงรายการล่าสุดก่อน."""

    requests = (
        await session.scalars(
            select(ServiceRequest)
            .options(selectinload(ServiceRequest.location))
            .where(ServiceRequest.request_type == RequestType.REPAIR)
            .order_by(
                ServiceRequest.created_at.desc(),
                ServiceRequest.id.desc(),
            )
        )
    ).all()

    return list(requests)


class RepairRequestNotFoundError(LookupError):
    """ไม่พบ repair request ที่ต้องการ."""


async def get_repair_request_detail(
    session: AsyncSession,
    request_id: UUID,
) -> ServiceRequest:
    """ดึงรายละเอียด repair request พร้อม location และ images."""

    request = await session.scalar(
        select(ServiceRequest)
        .options(
            selectinload(ServiceRequest.location),
            selectinload(ServiceRequest.images),
        )
        .where(
            ServiceRequest.id == request_id,
            ServiceRequest.request_type == RequestType.REPAIR,
        )
    )

    if request is None:
        raise RepairRequestNotFoundError("Repair request not found")

    return request