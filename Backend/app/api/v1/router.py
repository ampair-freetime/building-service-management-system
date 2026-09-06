"""รวม endpoint เวอร์ชัน 1 เพื่อให้ main application ลงทะเบียนในจุดเดียว."""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, found_item, lost_found_clerk, lost_item, staff

api_router = APIRouter()

# auth และ staff แยก namespace ตามหน้าที่
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(
    lost_item.router,
    prefix="/guest/lost-items",
    tags=["guest lost items"],
)
api_router.include_router(
    found_item.router,
    prefix="/guest/found-items",
    tags=["guest found items"],
)
api_router.include_router(staff.router, prefix="/staff", tags=["staff"])

# lost and found สำหรับเจ้าหน้าที่ธุรการ
api_router.include_router(
    lost_found_clerk.router,
    prefix = "/lost-found",
    tags = ["lost-found"],
)
