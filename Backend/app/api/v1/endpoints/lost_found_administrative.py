from fastapi import APIRouter

from app.api.dependencies import AdministrativeStaff, DbSession
from app.schemas.lost_found_administrative import PendingFoundItemResponse
from app.services.lost_found_administrative import list_pending_found_items

router = APIRouter()

@router.get(
    "/pending-found-items",
    response_model = list[PendingFoundItemResponse],
)

async def get_pending_found_items(
    session: DbSession,
    _: AdministrativeStaff,
) -> list[PendingFoundItemResponse]:
     """ คืนรายการของที่พบซึ่งกำลังรอเจ้าหน้าที่ธุรการตรวจสอบ"""
     return await list_pending_found_items(session)