"""รวม endpoint เวอร์ชัน 1 เพื่อให้ main application ลงทะเบียนในจุดเดียว."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, staff

api_router = APIRouter()

# health ไม่มี prefix เพิ่มเติม ส่วน auth และ staff แยก namespace ตามหน้าที่
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(staff.router, prefix="/staff", tags=["staff"])
