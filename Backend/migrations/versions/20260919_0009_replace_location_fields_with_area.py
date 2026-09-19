"""แทนที่ building/room/area_type ด้วย area เดียว

Revision ID: 20260919_0009
Revises: 20260919_0008
Create Date: 2026-09-19
"""

import sqlalchemy as sa
from alembic import op

revision: str = "20260919_0009"
down_revision: str | None = "20260919_0008"
branch_labels: str | None = None
depends_on: str | None = None

locations = sa.table(
    "locations",
    sa.column("building", sa.String()),
    sa.column("room", sa.String()),
    sa.column("area_type", sa.String()),
    sa.column("area", sa.String()),
)


def upgrade() -> None:
    # เพิ่มเป็น nullable ก่อน เพราะแถวเดิมยังไม่มีค่า area ให้ NOT NULL ตั้งแต่แรกไม่ได้
    op.add_column("locations", sa.Column("area", sa.String(length=100), nullable=True))
    # room เดิมเก็บเฉพาะเลข/ชื่อห้อง จึงเติมคำนำหน้าให้เป็นข้อความพร้อมแสดงผล
    # ถ้าไม่มี room ให้เลือก area_type แล้วจึง fallback ไป building ตามลำดับ
    op.execute(
        sa.update(locations).values(
            area=sa.case(
                (
                    locations.c.room.isnot(None),
                    sa.literal("ห้อง ") + locations.c.room,
                ),
                else_=sa.func.coalesce(locations.c.area_type, locations.c.building),
            )
        )
    )
    op.alter_column("locations", "area", nullable=False)
    op.drop_column("locations", "building")
    op.drop_column("locations", "room")
    op.drop_column("locations", "area_type")


def downgrade() -> None:
    # Lossy: room/area_type เดิมถูกรวมเป็น area ไปแล้ว ดึงกลับแยกค่าไม่ได้
    op.add_column("locations", sa.Column("building", sa.String(length=100), nullable=True))
    op.add_column("locations", sa.Column("room", sa.String(length=100), nullable=True))
    op.add_column("locations", sa.Column("area_type", sa.String(length=50), nullable=True))
    # เก็บ area ไว้ใน building ซึ่งยาวเท่ากันและเป็น NOT NULL ใน schema เดิม
    # เมื่อ upgrade ซ้ำ ค่าเดิมจะ fallback จาก building กลับมาโดยไม่เติม "ห้อง " ซ้ำ
    op.execute(sa.update(locations).values(building=locations.c.area))
    op.alter_column("locations", "building", nullable=False)
    op.drop_column("locations", "area")
