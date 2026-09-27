"""ทำ floor ให้อยู่ในรูปแบบเดียวกันและกัน (floor, area) ซ้ำด้วย unique index

Revision ID: 20260924_0011
Revises: 20260923_0010
Create Date: 2026-09-24
"""

import re

import sqlalchemy as sa
from alembic import op

revision: str = "20260924_0011"
down_revision: str | None = "20260923_0010"
branch_labels: str | None = None
depends_on: str | None = None

INDEX_NAME = "uq_locations_floor_area"

locations = sa.table(
    "locations",
    sa.column("id", sa.Integer),
    sa.column("floor", sa.String()),
    sa.column("area", sa.String()),
)

# คัดลอกกฎจาก app.schemas.admin_location ไว้ เพื่อให้ migration ให้ผลเหมือนเดิมแม้กฎในแอปเปลี่ยนภายหลัง
_FLOOR_PREFIX = re.compile(r"^(?:ชั้น|floor|fl(?:\.|(?=[\s\d])))\s*", re.IGNORECASE)


def _normalize_floor(value: str | None) -> str | None:
    if value is None:
        return None
    text = " ".join(value.split())
    if not text:
        return None
    # ข้อมูลเก่าที่เหลือแค่คำนำหน้าให้คงคำเดิมไว้แทนการ error เพราะเลือกค่าแทนให้ไม่ได้
    text = _FLOOR_PREFIX.sub("", text) or text
    if text.isdecimal():
        text = str(int(text))
    return text.upper()


def upgrade() -> None:
    connection = op.get_bind()
    column_names = {column["name"] for column in sa.inspect(connection).get_columns("locations")}

    # Some existing deployments were stamped at a merged revision while retaining
    # the pre-area location schema. Bring that schema forward here before the
    # normalisation below, so upgrade remains safe for both database histories.
    if "area" not in column_names:
        op.add_column("locations", sa.Column("area", sa.String(length=100), nullable=True))
        legacy_locations = sa.table(
            "locations",
            sa.column("building", sa.String()),
            sa.column("room", sa.String()),
            sa.column("area_type", sa.String()),
            sa.column("area", sa.String()),
        )
        if "area_type" in column_names and "building" in column_names:
            fallback = sa.func.coalesce(
                legacy_locations.c.area_type, legacy_locations.c.building
            )
        elif "area_type" in column_names:
            fallback = legacy_locations.c.area_type
        elif "building" in column_names:
            fallback = legacy_locations.c.building
        else:
            fallback = sa.literal("Unknown area")
        area_value = (
            sa.case(
                (legacy_locations.c.room.is_not(None), sa.literal("ห้อง ") + legacy_locations.c.room),
                else_=fallback,
            )
            if "room" in column_names
            else fallback
        )
        connection.execute(sa.update(legacy_locations).values(area=area_value))
        op.alter_column("locations", "area", nullable=False)
        for column_name in ("building", "room", "area_type"):
            if column_name in column_names:
                op.drop_column("locations", column_name)

    rows = connection.execute(sa.select(locations.c.id, locations.c.floor)).all()
    for location_id, floor in rows:
        normalized = _normalize_floor(floor)
        if normalized != floor:
            connection.execute(
                sa.update(locations)
                .where(locations.c.id == location_id)
                .values(floor=normalized)
            )

    # ไม่ merge แถวซ้ำให้เอง เพราะแต่ละแถวมี QR ที่อาจติดป้ายแล้วและมี FK จากงานต่างๆ
    duplicates = connection.execute(
        sa.select(
            locations.c.floor,
            locations.c.area,
            sa.func.count().label("total"),
        )
        # GROUP BY ถือว่า NULL อยู่กลุ่มเดียวกัน จึงจับ floor ว่างที่ซ้ำได้ด้วย
        .group_by(locations.c.floor, locations.c.area)
        .having(sa.func.count() > 1)
    ).all()
    if duplicates:
        details = ", ".join(
            f"{floor or '-'} / {area} ({total} rows)" for floor, area, total in duplicates
        )
        raise RuntimeError(
            f"Duplicate locations after normalizing floor; resolve them first: {details}"
        )

    op.create_index(
        INDEX_NAME,
        "locations",
        [sa.text("coalesce(floor, '')"), "area"],
        unique=True,
    )


def downgrade() -> None:
    # Lossy: ค่า floor เดิมก่อน normalize (เช่น "ชั้น 01") ไม่ได้เก็บไว้ จึงคืนได้แค่ index
    op.drop_index(INDEX_NAME, table_name="locations")
