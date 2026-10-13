"""กันสถานที่ซ้ำโดยไม่แยกตัวพิมพ์ใหญ่และตัวพิมพ์เล็ก

Revision ID: 20261012_0023
Revises: 20261010_0022
Create Date: 2026-10-12
"""

import sqlalchemy as sa
from alembic import op

revision = "20261012_0023"
down_revision = "20261010_0022"
branch_labels = None
depends_on = None

INDEX_NAME = "uq_locations_floor_area"


def upgrade() -> None:
    connection = op.get_bind()
    locations = sa.table(
        "locations",
        sa.column("floor", sa.String()),
        sa.column("area", sa.String()),
    )

    # ไม่รวมแถวให้เอง เพราะแต่ละสถานที่อาจมี QR และคำร้องที่อ้างอิงอยู่แล้ว
    duplicates = connection.execute(
        sa.select(
            sa.func.lower(sa.func.coalesce(locations.c.floor, "")).label("floor_key"),
            sa.func.lower(locations.c.area).label("area_key"),
            sa.func.count().label("total"),
        )
        .group_by(
            sa.func.lower(sa.func.coalesce(locations.c.floor, "")),
            sa.func.lower(locations.c.area),
        )
        .having(sa.func.count() > 1)
    ).all()
    if duplicates:
        details = ", ".join(
            f"{floor or '-'} / {area} ({total} rows)"
            for floor, area, total in duplicates
        )
        raise RuntimeError(
            "Duplicate locations ignoring letter case; resolve them first: " + details
        )

    op.drop_index(INDEX_NAME, table_name="locations")
    op.create_index(
        INDEX_NAME,
        "locations",
        [sa.text("lower(coalesce(floor, ''))"), sa.text("lower(area)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="locations")
    op.create_index(
        INDEX_NAME,
        "locations",
        [sa.text("coalesce(floor, '')"), "area"],
        unique=True,
    )
