"""ลบ staff_code เพราะพนักงานเข้าสู่ระบบด้วยอีเมลอย่างเดียว

Revision ID: 20260924_0012
Revises: 20260924_0011
Create Date: 2026-09-24
"""

import sqlalchemy as sa
from alembic import op

revision: str = "20260924_0012"
down_revision: str | None = "20260924_0011"
branch_labels: str | None = None
depends_on: str | None = None

INDEX_NAME = "ix_staff_staff_code"

staff = sa.table(
    "staff",
    sa.column("id", sa.Uuid),
    sa.column("email", sa.String()),
    sa.column("staff_code", sa.String()),
)


def upgrade() -> None:
    connection = op.get_bind()
    # อีเมลกลายเป็นช่องทางล็อกอินเดียว จึงต้องไม่ซ้ำกันแม้ต่างแค่ตัวพิมพ์
    duplicates = (
        connection.execute(
            sa.select(sa.func.lower(staff.c.email))
            .group_by(sa.func.lower(staff.c.email))
            .having(sa.func.count() > 1)
        )
        .scalars()
        .all()
    )
    if duplicates:
        raise RuntimeError(
            "Staff emails differ only by letter case; resolve them first: "
            + ", ".join(duplicates)
        )
    # บัญชีที่ seed ก่อนมี normalize อาจมีตัวพิมพ์ใหญ่ ซึ่งล็อกอินไม่ได้เพราะเทียบด้วยตัวพิมพ์เล็ก
    connection.execute(
        sa.update(staff)
        .where(staff.c.email != sa.func.lower(staff.c.email))
        .values(email=sa.func.lower(staff.c.email))
    )

    op.drop_index(INDEX_NAME, table_name="staff")
    with op.batch_alter_table("staff") as batch:
        batch.drop_column("staff_code")


def downgrade() -> None:
    # Lossy: รหัสเดิมหายไปแล้ว จึงสร้างรหัสใหม่จาก id ให้ไม่ซ้ำ แล้วค่อยบังคับ NOT NULL
    with op.batch_alter_table("staff") as batch:
        batch.add_column(sa.Column("staff_code", sa.String(length=30), nullable=True))
    connection = op.get_bind()
    for (staff_id,) in connection.execute(sa.select(staff.c.id)).all():
        connection.execute(
            sa.update(staff)
            .where(staff.c.id == staff_id)
            .values(staff_code=f"STAFF-{staff_id.hex[:12].upper()}")
        )
    with op.batch_alter_table("staff") as batch:
        batch.alter_column("staff_code", existing_type=sa.String(length=30), nullable=False)
    op.create_index(INDEX_NAME, "staff", ["staff_code"], unique=True)
