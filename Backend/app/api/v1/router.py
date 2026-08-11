"""รวม endpoint เวอร์ชัน 1 เพื่อให้ main application ลงทะเบียนในจุดเดียว."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, staff

api_router = APIRouter()

# auth และ staff แยก namespace ตามหน้าที่
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(staff.router, prefix="/staff", tags=["staff"])
